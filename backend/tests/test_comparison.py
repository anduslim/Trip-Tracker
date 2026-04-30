from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.flight_entry import FlightEntry
from app.models.holiday import Holiday
from app.models.price_snapshot import PriceSnapshot
from app.models.user import User
from app.security import hash_password
from app.services.comparison_engine import build_comparison


def _entry(holiday_id: int, origin: str, dest: str, price: str) -> FlightEntry:
    return FlightEntry(
        id=hash((holiday_id, origin, dest, price)) & 0x7FFFFFFF,
        holiday_id=holiday_id,
        origin_iata=origin,
        destination_iata=dest,
        depart_date=date(2026, 10, 1),
        passengers=1,
        source="manual",
        initial_price=Decimal(price),
        latest_price=Decimal(price),
        currency="USD",
    )


def test_build_comparison_groups_and_picks_cheapest_route() -> None:
    entries = [
        _entry(1, "SFO", "HND", "1200"),
        _entry(1, "SFO", "HND", "1100"),
        _entry(1, "LAX", "NRT", "900"),
    ]
    result = build_comparison(entries, snapshots_by_entry={})
    routes = sorted(result.route_groups, key=lambda g: (g.origin, g.destination))
    assert len(routes) == 2
    sfo_hnd = next(g for g in routes if g.origin == "SFO")
    assert sfo_hnd.entry_count == 2
    assert sfo_hnd.min_price == Decimal("1100")
    assert sfo_hnd.max_price == Decimal("1200")
    assert result.insights.cheapest_route is not None
    assert result.insights.cheapest_route["origin"] == "LAX"


def test_build_comparison_finds_biggest_drop_30d() -> None:
    e = _entry(1, "SFO", "HND", "900")
    now = datetime.now(UTC)
    snapshots = [
        PriceSnapshot(
            id=1,
            flight_entry_id=e.id,
            price=Decimal("1200"),
            currency="USD",
            source="manual",
            captured_at=now - timedelta(days=10),
        ),
        PriceSnapshot(
            id=2,
            flight_entry_id=e.id,
            price=Decimal("900"),
            currency="USD",
            source="manual",
            captured_at=now - timedelta(days=1),
        ),
    ]
    result = build_comparison([e], {e.id: snapshots})
    assert result.insights.biggest_drop_30d is not None
    assert result.insights.biggest_drop_30d["origin"] == "SFO"
    # 25% drop from 1200 to 900
    assert round(result.insights.biggest_drop_30d["delta_pct"], 1) == -25.0


@pytest.mark.asyncio
async def test_comparison_endpoint(authed_client: AsyncClient, db) -> None:
    user = (await db.execute(__import__("sqlalchemy").select(User).where(User.email == "u@example.com"))).scalar_one()
    holiday = Holiday(user_id=user.id, name="X", currency="USD", destinations=[])
    db.add(holiday)
    await db.flush()
    db.add_all(
        [
            FlightEntry(
                holiday_id=holiday.id,
                origin_iata="SFO",
                destination_iata="HND",
                depart_date=date(2026, 10, 1),
                passengers=1,
                source="manual",
                initial_price=Decimal("1200"),
                latest_price=Decimal("1200"),
                currency="USD",
            ),
            FlightEntry(
                holiday_id=holiday.id,
                origin_iata="LAX",
                destination_iata="NRT",
                depart_date=date(2026, 10, 1),
                passengers=1,
                source="manual",
                initial_price=Decimal("900"),
                latest_price=Decimal("900"),
                currency="USD",
            ),
        ]
    )
    await db.commit()

    r = await authed_client.get(f"/api/holidays/{holiday.id}/flights/comparison")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["route_groups"]) == 2
    assert body["insights"]["cheapest_route"]["origin"] == "LAX"
