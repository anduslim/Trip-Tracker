from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbDep
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.schemas.holiday import (
    HolidayCreate,
    HolidayDetail,
    HolidayResponse,
    HolidaySummary,
    HolidayUpdate,
)

router = APIRouter()


async def _get_owned_holiday(db, user_id: int, holiday_id: int, *, with_entries: bool = False) -> Holiday:
    stmt = select(Holiday).where(Holiday.id == holiday_id, Holiday.user_id == user_id)
    if with_entries:
        stmt = stmt.options(selectinload(Holiday.flight_entries))
    result = await db.execute(stmt)
    holiday = result.scalar_one_or_none()
    if holiday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return holiday


@router.get("", response_model=list[HolidaySummary])
async def list_holidays(db: DbDep, current_user: CurrentUser) -> list[HolidaySummary]:
    stmt = (
        select(
            Holiday,
            func.count(FlightEntry.id).label("entry_count"),
            func.min(FlightEntry.latest_price).label("lowest_price"),
        )
        .outerjoin(FlightEntry, FlightEntry.holiday_id == Holiday.id)
        .where(Holiday.user_id == current_user.id)
        .group_by(Holiday.id)
        .order_by(Holiday.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    out: list[HolidaySummary] = []
    for holiday, entry_count, lowest in rows:
        out.append(
            HolidaySummary.model_validate(
                {
                    **{c.name: getattr(holiday, c.name) for c in Holiday.__table__.columns},
                    "flight_entry_count": entry_count or 0,
                    "lowest_current_price": lowest,
                }
            )
        )
    return out


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(payload: HolidayCreate, db: DbDep, current_user: CurrentUser) -> Holiday:
    holiday = Holiday(
        user_id=current_user.id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        destinations=[d.model_dump() for d in payload.destinations],
        notes=payload.notes,
        currency=payload.currency,
        price_change_threshold_pct=payload.price_change_threshold_pct,
        price_change_threshold_abs=payload.price_change_threshold_abs,
    )
    db.add(holiday)
    await db.commit()
    await db.refresh(holiday)
    return holiday


@router.get("/{holiday_id}", response_model=HolidayDetail)
async def get_holiday(holiday_id: int, db: DbDep, current_user: CurrentUser) -> Holiday:
    return await _get_owned_holiday(db, current_user.id, holiday_id, with_entries=True)


@router.patch("/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: int, payload: HolidayUpdate, db: DbDep, current_user: CurrentUser
) -> Holiday:
    holiday = await _get_owned_holiday(db, current_user.id, holiday_id)
    data = payload.model_dump(exclude_unset=True)
    if "destinations" in data and data["destinations"] is not None:
        data["destinations"] = [d.model_dump() if hasattr(d, "model_dump") else d for d in data["destinations"]]
    for key, value in data.items():
        setattr(holiday, key, value)
    await db.commit()
    await db.refresh(holiday)
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(holiday_id: int, db: DbDep, current_user: CurrentUser) -> None:
    holiday = await _get_owned_holiday(db, current_user.id, holiday_id)
    await db.delete(holiday)
    await db.commit()
