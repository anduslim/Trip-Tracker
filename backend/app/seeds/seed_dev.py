"""Seed a demo user, holiday, and a couple of flight entries.

Idempotent: re-running won't duplicate the demo user/holiday.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.models.user import User
from app.security import hash_password

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"


async def seed() -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name="Demo Traveller",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"Created demo user {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print(f"Demo user already exists ({DEMO_EMAIL})")

        result = await db.execute(
            select(Holiday).where(Holiday.user_id == user.id, Holiday.name == "Japan 2026")
        )
        holiday = result.scalar_one_or_none()
        if holiday is None:
            holiday = Holiday(
                user_id=user.id,
                name="Japan 2026",
                start_date=date(2026, 10, 1),
                end_date=date(2026, 10, 14),
                destinations=[
                    {"city": "Tokyo", "iata": "HND", "country": "JP"},
                    {"city": "Kyoto", "iata": None, "country": "JP"},
                ],
                notes="Two weeks: Tokyo + Kyoto.",
                currency="USD",
            )
            db.add(holiday)
            await db.commit()
            await db.refresh(holiday)

            entry = FlightEntry(
                holiday_id=holiday.id,
                origin_iata="SFO",
                destination_iata="HND",
                depart_date=date(2026, 10, 1),
                return_date=date(2026, 10, 14),
                airline_code="UA",
                airline_name="United Airlines",
                cabin="ECONOMY",
                passengers=1,
                source_url="https://www.google.com/travel/flights",
                source="manual",
                initial_price=Decimal("1200.00"),
                latest_price=Decimal("1180.00"),
                currency="USD",
                tracking_enabled=True,
                last_checked_at=datetime.now(UTC),
            )
            db.add(entry)
            await db.flush()
            base = datetime.now(UTC) - timedelta(days=4)
            for i, price in enumerate([Decimal("1200"), Decimal("1220"), Decimal("1190"), Decimal("1180")]):
                db.add(
                    PriceSnapshot(
                        flight_entry_id=entry.id,
                        price=price,
                        currency="USD",
                        source="manual",
                        captured_at=base + timedelta(days=i),
                    )
                )
            await db.commit()
            print("Created demo holiday 'Japan 2026' with one tracked flight.")
        else:
            print("Demo holiday already exists.")


if __name__ == "__main__":
    asyncio.run(seed())
