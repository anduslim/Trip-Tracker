from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FlightEntry(TimestampMixin, Base):
    __tablename__ = "flight_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    holiday_id: Mapped[int] = mapped_column(
        ForeignKey("holidays.id", ondelete="CASCADE"), index=True, nullable=False
    )
    origin_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    depart_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date)
    airline_code: Mapped[str | None] = mapped_column(String(3))
    airline_name: Mapped[str | None] = mapped_column(String(100))
    cabin: Mapped[str | None] = mapped_column(String(20))
    passengers: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    provider_offer_id: Mapped[str | None] = mapped_column(String(100))
    provider_offer_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    initial_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    latest_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    holiday: Mapped["Holiday"] = relationship(back_populates="flight_entries")  # noqa: F821
    snapshots: Mapped[list["PriceSnapshot"]] = relationship(  # noqa: F821
        back_populates="flight_entry",
        cascade="all, delete-orphan",
        order_by="PriceSnapshot.captured_at",
    )

    __table_args__ = (
        Index("ix_flight_entries_route", "origin_iata", "destination_iata"),
    )
