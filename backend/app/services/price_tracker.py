"""Price tracker: refresh tracked flight entries and create change notifications."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.models.flight_entry import FlightEntry
from app.models.notification import Notification
from app.models.price_snapshot import PriceSnapshot
from app.services.flight_provider import FlightProvider, ProviderError
from app.services.provider_registry import get_provider

log = logging.getLogger(__name__)


@dataclass
class PriceChange:
    delta: Decimal
    delta_pct: float
    direction: str  # 'drop' | 'rise' | 'flat'


def detect_change(
    previous: Decimal,
    current: Decimal,
    *,
    threshold_pct: float,
    threshold_abs: Decimal,
) -> PriceChange | None:
    """Return a PriceChange if the move exceeds either threshold."""
    if previous == 0:
        return None
    delta = current - previous
    pct = float(abs(delta) / previous * 100)
    abs_change = abs(delta)
    if pct < threshold_pct and abs_change < threshold_abs:
        return None
    direction = "drop" if delta < 0 else "rise" if delta > 0 else "flat"
    return PriceChange(delta=delta, delta_pct=float(delta / previous * 100), direction=direction)


def _resolve_thresholds(entry: FlightEntry, settings: Settings) -> tuple[float, Decimal]:
    holiday = entry.holiday
    pct = (
        float(holiday.price_change_threshold_pct)
        if getattr(holiday, "price_change_threshold_pct", None) is not None
        else settings.price_change_threshold_pct
    )
    abs_t = (
        Decimal(str(holiday.price_change_threshold_abs))
        if getattr(holiday, "price_change_threshold_abs", None) is not None
        else Decimal(str(settings.price_change_threshold_abs))
    )
    return pct, abs_t


async def refresh_entry(
    db: AsyncSession,
    entry: FlightEntry,
    *,
    provider: FlightProvider | None = None,
    settings: Settings | None = None,
) -> PriceSnapshot | None:
    settings = settings or get_settings()
    if not provider:
        provider = get_provider(entry.source if entry.source in {"amadeus", "serpapi"} else None)

    payload = entry.provider_offer_payload or {
        "origin_iata": entry.origin_iata,
        "destination_iata": entry.destination_iata,
        "depart_date": entry.depart_date.isoformat(),
        "return_date": entry.return_date.isoformat() if entry.return_date else None,
        "airline_code": entry.airline_code,
        "passengers": entry.passengers,
        "currency": entry.currency,
        "provider_offer_id": entry.provider_offer_id,
    }
    try:
        offer = await provider.reprice(payload)
    except ProviderError as e:
        log.warning("Reprice failed for entry %s: %s", entry.id, e)
        return None
    if offer is None:
        return None

    previous = Decimal(str(entry.latest_price))
    new_price = offer.price
    snapshot = PriceSnapshot(
        flight_entry_id=entry.id,
        price=new_price,
        currency=offer.currency,
        source=f"{provider.name}_reprice",
        raw_payload=offer.raw or None,
    )
    db.add(snapshot)
    entry.latest_price = new_price
    entry.currency = offer.currency
    entry.last_checked_at = datetime.now(UTC)

    pct, abs_t = _resolve_thresholds(entry, settings)
    change = detect_change(previous, new_price, threshold_pct=pct, threshold_abs=abs_t)
    if change and change.direction != "flat":
        verb = "dropped" if change.direction == "drop" else "rose"
        title = f"{entry.origin_iata}→{entry.destination_iata} {verb} {abs(change.delta_pct):.1f}%"
        body = (
            f"Price for {entry.origin_iata} → {entry.destination_iata} on "
            f"{entry.depart_date.isoformat()} {verb} from {entry.currency} {previous} "
            f"to {entry.currency} {new_price} (Δ {change.delta:+}, {change.delta_pct:+.1f}%)."
        )
        db.add(
            Notification(
                user_id=entry.holiday.user_id,
                holiday_id=entry.holiday_id,
                flight_entry_id=entry.id,
                type=f"price_{change.direction}",
                title=title,
                body=body,
                extra={
                    "previous_price": str(previous),
                    "new_price": str(new_price),
                    "delta": str(change.delta),
                    "delta_pct": change.delta_pct,
                    "currency": entry.currency,
                },
                email_status="pending",
            )
        )
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def refresh_due_entries(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings | None = None,
    batch_size: int = 50,
) -> int:
    """Refresh entries whose last_checked_at is older than the interval.
    Returns the number of entries refreshed."""
    settings = settings or get_settings()
    cutoff = datetime.now(UTC) - timedelta(minutes=settings.price_refresh_interval_minutes)
    refreshed = 0
    async with session_factory() as db:
        stmt = (
            select(FlightEntry)
            .where(
                FlightEntry.tracking_enabled.is_(True),
                FlightEntry.archived.is_(False),
                (FlightEntry.last_checked_at.is_(None)) | (FlightEntry.last_checked_at < cutoff),
            )
            .limit(batch_size)
        )
        entries = list((await db.execute(stmt)).scalars().all())
        # Eager-load .holiday once per entry; use a fresh session per entry for isolation.
    sem = asyncio.Semaphore(4)

    async def _process(entry_id: int) -> None:
        nonlocal refreshed
        async with sem, session_factory() as db:
            entry = await db.get(FlightEntry, entry_id)
            if entry is None:
                return
            await db.refresh(entry, attribute_names=["holiday"])
            snapshot = await refresh_entry(db, entry)
            if snapshot is not None:
                refreshed += 1

    await asyncio.gather(*(_process(e.id) for e in entries))
    return refreshed


async def prune_old_snapshots(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    older_than_days: int = 90,
) -> int:
    """Downsample snapshots older than `older_than_days` to one per day per
    flight entry (keep the most recent). Returns number of rows deleted."""
    from sqlalchemy import delete, func

    cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
    deleted = 0
    async with session_factory() as db:
        # Identify (entry_id, day) groups; keep the row with max(captured_at) per group, delete the rest.
        date_expr = func.date(PriceSnapshot.captured_at)
        rows = (
            await db.execute(
                select(
                    PriceSnapshot.id,
                    PriceSnapshot.flight_entry_id,
                    date_expr.label("day"),
                    PriceSnapshot.captured_at,
                ).where(PriceSnapshot.captured_at < cutoff)
            )
        ).all()
        keep_ids: set[int] = set()
        per_group: dict[tuple[int, str], tuple[int, datetime]] = {}
        for snap_id, entry_id, day, captured_at in rows:
            key = (entry_id, str(day))
            current = per_group.get(key)
            if current is None or captured_at > current[1]:
                per_group[key] = (snap_id, captured_at)
        keep_ids = {v[0] for v in per_group.values()}
        delete_ids = [snap_id for (snap_id, _, _, _) in rows if snap_id not in keep_ids]
        if delete_ids:
            await db.execute(delete(PriceSnapshot).where(PriceSnapshot.id.in_(delete_ids)))
            await db.commit()
            deleted = len(delete_ids)
    return deleted


async def dispatch_pending_emails(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings | None = None,
    batch_size: int = 50,
) -> int:
    """Send queued email notifications. Returns number sent."""
    from app.models.user import User
    from app.services.notifier import get_email_sender

    settings = settings or get_settings()
    sender = get_email_sender(settings)
    sent = 0
    async with session_factory() as db:
        stmt = (
            select(Notification)
            .where(Notification.email_status == "pending")
            .limit(batch_size)
        )
        rows = list((await db.execute(stmt)).scalars().all())
        for n in rows:
            n.email_status = "sending"
        await db.commit()
        for n in rows:
            user = await db.get(User, n.user_id)
            if user is None:
                n.email_status = "skipped"
                continue
            try:
                await sender.send(to=user.email, subject=n.title, text=n.body)
                n.email_status = "sent"
                n.email_sent_at = datetime.now(UTC)
                sent += 1
            except Exception as e:  # pragma: no cover - network errors
                log.warning("Email send failed for notification %s: %s", n.id, e)
                n.email_status = "failed"
        await db.commit()
    return sent
