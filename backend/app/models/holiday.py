from datetime import date
from typing import Any

from sqlalchemy import JSON, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Holiday(TimestampMixin, Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    destinations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    price_change_threshold_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    price_change_threshold_abs: Mapped[float | None] = mapped_column(Numeric(10, 2))

    user: Mapped["User"] = relationship(back_populates="holidays")  # noqa: F821
    flight_entries: Mapped[list["FlightEntry"]] = relationship(  # noqa: F821
        back_populates="holiday", cascade="all, delete-orphan"
    )
