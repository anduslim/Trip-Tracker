from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select

import app.routers.search as search_module
from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.models.user import User
from app.services.comparison_engine import build_comparison
from app.services.fake_provider import FakeFlightProvider
from app.services.flight_provider import NormalizedOffer


async def test_trip_duration_filters_results(authed_client: AsyncClient) -> None:
    # Construct three offers with different return dates -> different durations.
    offers = [
        NormalizedOffer(
            provider="fake",
            provider_offer_id=f"d{n}",
            origin_iata="SFO",
            destination_iata="HND",
            depart_date=date(2026, 10, 1),
            return_date=date(2026, 10, 1) + timedelta(days=n),
            airline_code="UA",
            airline_name="United",
            cabin="ECONOMY",
            passengers=1,
            price=Decimal("1000"),
            currency="USD",
        )
        for n in (5, 10, 21)
    ]
    fake = FakeFlightProvider(offers=offers)
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/flights",
            json={
                "origin": "SFO",
                "destination": "HND",
                "depart_date": "2026-10-01",
                "return_date": "2026-10-22",
                "min_duration_days": 7,
                "max_duration_days": 14,
            },
        )
        assert resp.status_code == 200
        # Only the 10-day option matches.
        out = resp.json()["offers"]
        assert len(out) == 1
        assert out[0]["return_date"] == "2026-10-11"
    finally:
        search_module.get_provider = original


def test_best_day_of_week_emits_only_with_enough_distinct_weekdays() -> None:
    holiday_id = 1
    # 5 entries spanning 4+ distinct weekdays for the SFO->HND route.
    entries = [
        _entry(holiday_id, date(2026, 10, d), Decimal(price))
        for d, price in [
            (5, "1000"),  # Mon
            (6, "950"),   # Tue
            (7, "900"),   # Wed (cheapest)
            (8, "1100"),  # Thu
            (9, "1050"),  # Fri
        ]
    ]
    result = build_comparison(entries, snapshots_by_entry={})
    bdow = result.insights.best_day_of_week
    assert len(bdow) == 1
    assert bdow[0]["best_day"] == "Wed"


def test_best_day_of_week_silent_when_few_weekdays() -> None:
    entries = [
        _entry(1, date(2026, 10, 5), Decimal("1000")),
        _entry(1, date(2026, 10, 12), Decimal("900")),
    ]
    result = build_comparison(entries, snapshots_by_entry={})
    assert result.insights.best_day_of_week == []


async def test_prune_old_snapshots_downsamples(db) -> None:
    from app.db import SessionLocal
    from app.security import hash_password
    from app.services.price_tracker import prune_old_snapshots

    user = User(email="p@p.com", password_hash=hash_password("password123"))
    db.add(user)
    await db.flush()
    holiday = Holiday(user_id=user.id, name="H", currency="USD", destinations=[])
    db.add(holiday)
    await db.flush()
    entry = FlightEntry(
        holiday_id=holiday.id,
        origin_iata="SFO",
        destination_iata="HND",
        depart_date=date(2026, 10, 1),
        passengers=1,
        source="manual",
        initial_price=Decimal("1000"),
        latest_price=Decimal("1000"),
        currency="USD",
    )
    db.add(entry)
    await db.flush()
    base = datetime.now(UTC) - timedelta(days=120)
    for i in range(5):
        db.add(
            PriceSnapshot(
                flight_entry_id=entry.id,
                price=Decimal("1000"),
                currency="USD",
                source="manual",
                captured_at=base + timedelta(hours=i),  # all same day
            )
        )
    db.add(
        PriceSnapshot(
            flight_entry_id=entry.id,
            price=Decimal("1000"),
            currency="USD",
            source="manual",
            captured_at=datetime.now(UTC),  # recent — should not be pruned
        )
    )
    await db.commit()

    factory = lambda: db.__class__(bind=db.bind, expire_on_commit=False)  # noqa: E731
    # Use the actual session factory the app uses; its engine is overridden in tests.
    from app import db as db_module

    deleted = await prune_old_snapshots(db_module.SessionLocal)
    # Out of 5 same-day old rows, 4 deleted; recent row untouched.
    assert deleted == 4

    rows = (
        await db.execute(select(PriceSnapshot).where(PriceSnapshot.flight_entry_id == entry.id))
    ).scalars().all()
    assert len(list(rows)) == 2


async def test_public_rate_limit_returns_429(client: AsyncClient, monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "3")
    get_settings.cache_clear()
    try:
        # Hit /api/public/share/<bogus> repeatedly. The endpoint itself returns
        # 410, but the limiter caps requests at 3 per minute.
        codes = [
            (await client.get("/api/public/share/nope")).status_code for _ in range(5)
        ]
        assert codes[:3] == [410, 410, 410]
        assert codes[-1] == 429
    finally:
        get_settings.cache_clear()


def _entry(holiday_id: int, depart: date, price: Decimal) -> FlightEntry:
    return FlightEntry(
        id=hash((holiday_id, depart, str(price))) & 0x7FFFFFFF,
        holiday_id=holiday_id,
        origin_iata="SFO",
        destination_iata="HND",
        depart_date=depart,
        passengers=1,
        source="manual",
        initial_price=price,
        latest_price=price,
        currency="USD",
    )
