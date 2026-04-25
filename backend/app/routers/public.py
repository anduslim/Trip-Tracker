from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import DbDep
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.services import share_service
from app.services.comparison_engine import build_comparison

router = APIRouter(prefix="/api/public/share", tags=["public"])


@router.get("/{token}")
async def public_share(token: str, db: DbDep) -> dict:
    try:
        holiday = await share_service.resolve(db, token)
    except share_service.ShareTokenInvalid:
        raise HTTPException(status.HTTP_410_GONE, detail="Share link is no longer active")

    full = await db.execute(
        select(Holiday)
        .where(Holiday.id == holiday.id)
        .options(selectinload(Holiday.flight_entries))
    )
    holiday = full.scalar_one()

    entries = list(holiday.flight_entries)
    snapshots_by_entry: dict[int, list[PriceSnapshot]] = {}
    if entries:
        snaps_q = await db.execute(
            select(PriceSnapshot).where(
                PriceSnapshot.flight_entry_id.in_([e.id for e in entries])
            )
        )
        for s in snaps_q.scalars().all():
            snapshots_by_entry.setdefault(s.flight_entry_id, []).append(s)

    comparison = build_comparison(entries, snapshots_by_entry).to_dict()

    return {
        "holiday": {
            "name": holiday.name,
            "start_date": holiday.start_date.isoformat() if holiday.start_date else None,
            "end_date": holiday.end_date.isoformat() if holiday.end_date else None,
            "destinations": holiday.destinations or [],
            "currency": holiday.currency,
        },
        "flight_entries": [
            {
                "id": e.id,
                "origin_iata": e.origin_iata,
                "destination_iata": e.destination_iata,
                "depart_date": e.depart_date.isoformat(),
                "return_date": e.return_date.isoformat() if e.return_date else None,
                "airline_name": e.airline_name,
                "cabin": e.cabin,
                "passengers": e.passengers,
                "initial_price": str(e.initial_price),
                "latest_price": str(e.latest_price),
                "currency": e.currency,
                "snapshots": [
                    {
                        "price": str(s.price),
                        "currency": s.currency,
                        "captured_at": s.captured_at.isoformat() if s.captured_at else None,
                    }
                    for s in sorted(snapshots_by_entry.get(e.id, []), key=lambda x: x.captured_at)
                ],
            }
            for e in entries
        ],
        "comparison": comparison,
    }
