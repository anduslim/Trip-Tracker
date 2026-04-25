from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class FlightEntryCreate(BaseModel):
    origin_iata: str = Field(min_length=3, max_length=3)
    destination_iata: str = Field(min_length=3, max_length=3)
    depart_date: date
    return_date: date | None = None
    airline_code: str | None = Field(default=None, max_length=3)
    airline_name: str | None = Field(default=None, max_length=100)
    cabin: str | None = Field(default=None, max_length=20)
    passengers: int = Field(default=1, ge=1, le=20)
    source_url: HttpUrl | None = None
    initial_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tracking_enabled: bool = True


class FlightEntryUpdate(BaseModel):
    airline_code: str | None = Field(default=None, max_length=3)
    airline_name: str | None = Field(default=None, max_length=100)
    cabin: str | None = Field(default=None, max_length=20)
    passengers: int | None = Field(default=None, ge=1, le=20)
    source_url: HttpUrl | None = None
    tracking_enabled: bool | None = None
    archived: bool | None = None


class FlightEntryResponse(BaseModel):
    id: int
    holiday_id: int
    origin_iata: str
    destination_iata: str
    depart_date: date
    return_date: date | None
    airline_code: str | None
    airline_name: str | None
    cabin: str | None
    passengers: int
    source_url: str | None
    source: str
    initial_price: Decimal
    latest_price: Decimal
    currency: str
    tracking_enabled: bool
    last_checked_at: datetime | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceSnapshotResponse(BaseModel):
    id: int
    flight_entry_id: int
    price: Decimal
    currency: str
    source: str
    captured_at: datetime

    class Config:
        from_attributes = True


class RefreshPriceRequest(BaseModel):
    price: Decimal = Field(ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
