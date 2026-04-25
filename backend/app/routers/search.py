from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbDep
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.schemas.flight import FlightEntryResponse
from app.schemas.search import (
    FlightSearchRequest,
    OfferResponse,
    SaveOfferRequest,
    SearchResponse,
)
from app.services.flight_provider import ProviderError, SearchQuery
from app.services.provider_registry import available_providers, get_provider

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/providers")
async def list_providers() -> dict[str, list[str]]:
    return {"providers": available_providers()}


@router.post("/flights", response_model=SearchResponse)
async def search_flights(
    payload: FlightSearchRequest, _user: CurrentUser
) -> SearchResponse:
    provider = get_provider(payload.provider)
    query = SearchQuery(
        origin=payload.origin,
        destination=payload.destination,
        depart_date=payload.depart_date,
        return_date=payload.return_date,
        passengers=payload.passengers,
        cabin=payload.cabin,
        currency=payload.currency,
        max_price=payload.max_price,
        max_results=payload.max_results,
    )
    try:
        offers = await provider.search(query)
    except ProviderError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    if payload.max_price is not None:
        offers = [o for o in offers if o.price <= payload.max_price]
    return SearchResponse(
        provider=provider.name,
        offers=[OfferResponse(**{k: v for k, v in o.to_dict().items() if k != "raw"}) for o in offers],
    )


@router.post(
    "/save-offer",
    response_model=FlightEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_offer(
    payload: SaveOfferRequest, db: DbDep, current_user: CurrentUser
) -> FlightEntry:
    holiday_q = await db.execute(
        select(Holiday).where(Holiday.id == payload.holiday_id, Holiday.user_id == current_user.id)
    )
    holiday = holiday_q.scalar_one_or_none()
    if holiday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    offer = payload.offer
    entry = FlightEntry(
        holiday_id=holiday.id,
        origin_iata=offer.origin_iata.upper(),
        destination_iata=offer.destination_iata.upper(),
        depart_date=offer.depart_date,
        return_date=offer.return_date,
        airline_code=offer.airline_code,
        airline_name=offer.airline_name,
        cabin=offer.cabin,
        passengers=offer.passengers,
        source_url=offer.deep_link,
        source=offer.provider,
        provider_offer_id=offer.provider_offer_id or None,
        provider_offer_payload=payload.raw_payload,
        initial_price=offer.price,
        latest_price=offer.price,
        currency=offer.currency.upper(),
        tracking_enabled=True,
        last_checked_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.flush()
    db.add(
        PriceSnapshot(
            flight_entry_id=entry.id,
            price=offer.price,
            currency=offer.currency.upper(),
            source=f"{offer.provider}_search",
        )
    )
    await db.commit()
    await db.refresh(entry)
    return entry


# Mark for static analyzers; suppress unused-import warning
_ = Decimal
