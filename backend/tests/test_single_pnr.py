from httpx import AsyncClient

import app.routers.search as search_module
from app.services.fake_provider import FakeFlightProvider


async def test_single_pnr_multi_city_returns_combined_offers(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/multi-city-single-pnr",
            json={
                "legs": [
                    {"origin": "SFO", "destination": "LHR", "depart_date": "2026-10-01"},
                    {"origin": "LHR", "destination": "CDG", "depart_date": "2026-10-08"},
                    {"origin": "CDG", "destination": "SFO", "depart_date": "2026-10-15"},
                ],
                "currency": "USD",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Two variants from fake (cheap = 450 each leg, full-fare = 550 each leg).
        assert len(body["offers"]) == 2
        first = body["offers"][0]
        assert len(first["legs"]) == 3
        # 450 * 3 = 1350.
        assert first["total_price"] == "1350"
        assert first["legs"][0]["origin_iata"] == "SFO"
        assert first["legs"][1]["origin_iata"] == "LHR"
        assert first["legs"][2]["destination_iata"] == "SFO"
    finally:
        search_module.get_provider = original


async def test_single_pnr_max_price_caps_total(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        # Cap at 500/leg * 3 legs = 1500. Only the 1350 variant fits.
        resp = await authed_client.post(
            "/api/search/multi-city-single-pnr",
            json={
                "legs": [
                    {"origin": "SFO", "destination": "LHR", "depart_date": "2026-10-01"},
                    {"origin": "LHR", "destination": "CDG", "depart_date": "2026-10-08"},
                    {"origin": "CDG", "destination": "SFO", "depart_date": "2026-10-15"},
                ],
                "currency": "USD",
                "max_price_per_leg": "500",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["offers"]) == 1
        assert body["offers"][0]["total_price"] == "1350"
    finally:
        search_module.get_provider = original
