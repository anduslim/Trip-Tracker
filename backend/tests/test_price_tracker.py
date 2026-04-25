from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.notification import Notification
from app.models.price_snapshot import PriceSnapshot
from app.models.user import User
from app.security import hash_password
from app.services.fake_provider import FakeFlightProvider
from app.services.price_tracker import detect_change, refresh_entry


def test_detect_change_below_threshold_returns_none() -> None:
    assert (
        detect_change(
            Decimal("100"),
            Decimal("103"),
            threshold_pct=5.0,
            threshold_abs=Decimal("10"),
        )
        is None
    )


def test_detect_change_above_pct_threshold() -> None:
    change = detect_change(
        Decimal("100"),
        Decimal("110"),
        threshold_pct=5.0,
        threshold_abs=Decimal("999"),
    )
    assert change is not None
    assert change.direction == "rise"
    assert round(change.delta_pct, 1) == 10.0


def test_detect_change_above_abs_threshold() -> None:
    change = detect_change(
        Decimal("1000"),
        Decimal("970"),
        threshold_pct=99.0,
        threshold_abs=Decimal("25"),
    )
    assert change is not None
    assert change.direction == "drop"


@pytest.mark.asyncio
async def test_refresh_entry_creates_snapshot_and_notification(db) -> None:
    user = User(email="t@t.com", password_hash=hash_password("password123"))
    db.add(user)
    await db.flush()
    holiday = Holiday(user_id=user.id, name="H", currency="USD", destinations=[])
    db.add(holiday)
    await db.flush()
    entry = FlightEntry(
        holiday_id=holiday.id,
        origin_iata="SFO",
        destination_iata="HND",
        depart_date=date(2026, 10, 1),
        passengers=1,
        source="fake",
        initial_price=Decimal("1000.00"),
        latest_price=Decimal("1000.00"),
        currency="USD",
        tracking_enabled=True,
        last_checked_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry, attribute_names=["holiday"])

    fake = FakeFlightProvider(reprice_value=Decimal("850.00"))
    snap = await refresh_entry(db, entry, provider=fake)
    assert snap is not None
    assert snap.price == Decimal("850.00")

    snaps = (await db.execute(select(PriceSnapshot).where(PriceSnapshot.flight_entry_id == entry.id))).scalars().all()
    assert len(list(snaps)) == 1

    notifs = (await db.execute(select(Notification).where(Notification.flight_entry_id == entry.id))).scalars().all()
    notifs = list(notifs)
    assert len(notifs) == 1
    assert notifs[0].type == "price_drop"
    assert notifs[0].email_status == "pending"
