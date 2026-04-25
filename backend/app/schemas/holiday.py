from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class Destination(BaseModel):
    city: str
    iata: str | None = None
    country: str | None = None


class HolidayBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    destinations: list[Destination] = Field(default_factory=list)
    notes: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    price_change_threshold_pct: Decimal | None = None
    price_change_threshold_abs: Decimal | None = None


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    destinations: list[Destination] | None = None
    notes: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price_change_threshold_pct: Decimal | None = None
    price_change_threshold_abs: Decimal | None = None


class HolidayResponse(HolidayBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HolidaySummary(HolidayResponse):
    flight_entry_count: int = 0
    lowest_current_price: Decimal | None = None


class HolidayDetail(HolidayResponse):
    flight_entries: list["FlightEntryResponse"] = Field(default_factory=list)


# Avoid circular import for forward ref
from app.schemas.flight import FlightEntryResponse  # noqa: E402

HolidayDetail.model_rebuild()
