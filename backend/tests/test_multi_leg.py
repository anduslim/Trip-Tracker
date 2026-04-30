from datetime import date
from decimal import Decimal

from httpx import AsyncClient

import app.routers.search as search_module
from app.services.fake_provider import FakeFlightProvider


async def test_multi_leg_search_runs_each_leg(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/multi-leg",
            json={
                "legs": [
                    {"origin": "SFO", "destination": "LHR", "depart_date": "2026-10-01"},
                    {"origin": "LHR", "destination": "CDG", "depart_date": "2026-10-08"},
                    {"origin": "CDG", "destination": "SFO", "depart_date": "2026-10-15"},
                ],
                "passengers": 1,
                "currency": "USD",
                "max_results_per_leg": 3,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["provider"] == "fake"
        assert len(body["legs"]) == 3
        # Fake provider returns 3 offers per leg starting at 500.
        assert all(len(leg["offers"]) == 3 for leg in body["legs"])
        # Total min price = 500 + 500 + 500 = 1500.
        assert body["total_min_price"] == "1500.00"
        # Verify routes were forwarded correctly.
        assert body["legs"][1]["origin"] == "LHR"
        assert body["legs"][1]["destination"] == "CDG"
    finally:
        search_module.get_provider = original


async def test_multi_leg_search_max_price_filter(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/multi-leg",
            json={
                "legs": [
                    {"origin": "SFO", "destination": "LHR", "depart_date": "2026-10-01"},
                    {"origin": "LHR", "destination": "SFO", "depart_date": "2026-10-15"},
                ],
                "max_price_per_leg": "525",
                "currency": "USD",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        # Only the 500 offer fits the cap on each leg.
        assert all(len(leg["offers"]) == 1 for leg in body["legs"])
        assert body["total_min_price"] == "1000.00"
    finally:
        search_module.get_provider = original


async def test_multi_leg_requires_at_least_two(authed_client: AsyncClient) -> None:
    resp = await authed_client.post(
        "/api/search/multi-leg",
        json={
            "legs": [{"origin": "SFO", "destination": "LHR", "depart_date": "2026-10-01"}],
        },
    )
    assert resp.status_code == 422
    # Use the imports so they're not flagged unused.
    _ = (date, Decimal)
