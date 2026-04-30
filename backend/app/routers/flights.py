from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbDep
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.schemas.flight import (
    FlightEntryCreate,
    FlightEntryResponse,
    FlightEntryUpdate,
    PriceSnapshotResponse,
    RefreshPriceRequest,
)
from app.services.comparison_engine import build_comparison

router = APIRouter(prefix="/api/holidays/{holiday_id}/flights")


async def _owned_holiday(db, user_id: int, holiday_id: int) -> Holiday:
    result = await db.execute(
        select(Holiday).where(Holiday.id == holiday_id, Holiday.user_id == user_id)
    )
    holiday = result.scalar_one_or_none()
    if holiday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return holiday


async def _owned_entry(db, user_id: int, holiday_id: int, entry_id: int) -> FlightEntry:
    await _owned_holiday(db, user_id, holiday_id)
    result = await db.execute(
        select(FlightEntry).where(
            FlightEntry.id == entry_id, FlightEntry.holiday_id == holiday_id
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Flight entry not found")
    return entry


@router.get("", response_model=list[FlightEntryResponse])
async def list_entries(
    holiday_id: int, db: DbDep, current_user: CurrentUser
) -> list[FlightEntry]:
    await _owned_holiday(db, current_user.id, holiday_id)
    result = await db.execute(
        select(FlightEntry)
        .where(FlightEntry.holiday_id == holiday_id)
        .order_by(FlightEntry.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=FlightEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    holiday_id: int, payload: FlightEntryCreate, db: DbDep, current_user: CurrentUser
) -> FlightEntry:
    await _owned_holiday(db, current_user.id, holiday_id)
    entry = FlightEntry(
        holiday_id=holiday_id,
        origin_iata=payload.origin_iata.upper(),
        destination_iata=payload.destination_iata.upper(),
        depart_date=payload.depart_date,
        return_date=payload.return_date,
        airline_code=payload.airline_code,
        airline_name=payload.airline_name,
        cabin=payload.cabin,
        passengers=payload.passengers,
        source_url=str(payload.source_url) if payload.source_url else None,
        source="manual",
        initial_price=payload.initial_price,
        latest_price=payload.initial_price,
        currency=payload.currency.upper(),
        tracking_enabled=payload.tracking_enabled,
        last_checked_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.flush()
    snapshot = PriceSnapshot(
        flight_entry_id=entry.id,
        price=payload.initial_price,
        currency=payload.currency.upper(),
        source="manual",
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/comparison")
async def comparison(
    holiday_id: int, db: DbDep, current_user: CurrentUser
) -> dict:
    await _owned_holiday(db, current_user.id, holiday_id)
    entries = list(
        (
            await db.execute(
                select(FlightEntry).where(FlightEntry.holiday_id == holiday_id)
            )
        )
        .scalars()
        .all()
    )
    snapshots_by_entry: dict[int, list[PriceSnapshot]] = {}
    if entries:
        snaps_q = await db.execute(
            select(PriceSnapshot).where(
                PriceSnapshot.flight_entry_id.in_([e.id for e in entries])
            )
        )
        for s in snaps_q.scalars().all():
            snapshots_by_entry.setdefault(s.flight_entry_id, []).append(s)
    return build_comparison(entries, snapshots_by_entry).to_dict()


@router.get("/{entry_id}", response_model=FlightEntryResponse)
async def get_entry(
    holiday_id: int, entry_id: int, db: DbDep, current_user: CurrentUser
) -> FlightEntry:
    return await _owned_entry(db, current_user.id, holiday_id, entry_id)


@router.patch("/{entry_id}", response_model=FlightEntryResponse)
async def update_entry(
    holiday_id: int,
    entry_id: int,
    payload: FlightEntryUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> FlightEntry:
    entry = await _owned_entry(db, current_user.id, holiday_id, entry_id)
    data = payload.model_dump(exclude_unset=True)
    if "source_url" in data and data["source_url"] is not None:
        data["source_url"] = str(data["source_url"])
    for key, value in data.items():
        setattr(entry, key, value)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    holiday_id: int, entry_id: int, db: DbDep, current_user: CurrentUser
) -> None:
    entry = await _owned_entry(db, current_user.id, holiday_id, entry_id)
    await db.delete(entry)
    await db.commit()


@router.get("/{entry_id}/snapshots", response_model=list[PriceSnapshotResponse])
async def list_snapshots(
    holiday_id: int, entry_id: int, db: DbDep, current_user: CurrentUser
) -> list[PriceSnapshot]:
    await _owned_entry(db, current_user.id, holiday_id, entry_id)
    result = await db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.flight_entry_id == entry_id)
        .order_by(PriceSnapshot.captured_at.asc())
    )
    return list(result.scalars().all())


@router.post(
    "/{entry_id}/refresh",
    response_model=PriceSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def refresh_price(
    holiday_id: int,
    entry_id: int,
    payload: RefreshPriceRequest,
    db: DbDep,
    current_user: CurrentUser,
) -> PriceSnapshot:
    """Phase 1: caller supplies the new price (e.g. read from a website).

    Phase 2 will call the provider's reprice() instead.
    """
    entry = await _owned_entry(db, current_user.id, holiday_id, entry_id)
    currency = (payload.currency or entry.currency).upper()
    snapshot = PriceSnapshot(
        flight_entry_id=entry.id,
        price=payload.price,
        currency=currency,
        source="manual",
    )
    db.add(snapshot)
    entry.latest_price = payload.price
    entry.currency = currency
    entry.last_checked_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot
