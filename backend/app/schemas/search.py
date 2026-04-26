from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class FlightSearchRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    depart_date: date
    return_date: date | None = None
    passengers: int = Field(default=1, ge=1, le=20)
    cabin: str | None = Field(default=None, max_length=20)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    max_price: Decimal | None = None
    max_results: int = Field(default=10, ge=1, le=50)
    provider: str | None = None  # 'amadeus' | 'serpapi' | 'fake' | None=default
    min_duration_days: int | None = Field(default=None, ge=1, le=365)
    max_duration_days: int | None = Field(default=None, ge=1, le=365)


class OfferResponse(BaseModel):
    provider: str
    provider_offer_id: str
    origin_iata: str
    destination_iata: str
    depart_date: date
    return_date: date | None
    airline_code: str | None
    airline_name: str | None
    cabin: str | None
    passengers: int
    price: Decimal
    currency: str
    deep_link: str | None = None


class SearchResponse(BaseModel):
    provider: str
    offers: list[OfferResponse]


class SaveOfferRequest(BaseModel):
    holiday_id: int
    offer: OfferResponse
    raw_payload: dict[str, Any] | None = None


class LegRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    depart_date: date


class MultiLegSearchRequest(BaseModel):
    legs: list[LegRequest] = Field(min_length=2, max_length=8)
    passengers: int = Field(default=1, ge=1, le=20)
    cabin: str | None = Field(default=None, max_length=20)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    max_price_per_leg: Decimal | None = None
    max_results_per_leg: int = Field(default=5, ge=1, le=20)
    provider: str | None = None


class LegResult(BaseModel):
    origin: str
    destination: str
    depart_date: date
    offers: list[OfferResponse]
    error: str | None = None


class MultiLegSearchResponse(BaseModel):
    provider: str
    legs: list[LegResult]
    total_min_price: Decimal | None = None
    currency: str
