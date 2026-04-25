from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    flight_entry_id: Mapped[int] = mapped_column(
        ForeignKey("flight_entries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    flight_entry: Mapped["FlightEntry"] = relationship(back_populates="snapshots")  # noqa: F821

    __table_args__ = (
        Index("ix_price_snapshots_entry_captured", "flight_entry_id", "captured_at"),
    )
