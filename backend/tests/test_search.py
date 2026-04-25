from httpx import AsyncClient

from app.main import app
from app.services.fake_provider import FakeFlightProvider
from app.services.provider_registry import get_provider


async def test_search_flights_uses_provider(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()
    app.dependency_overrides[get_provider] = lambda: fake  # not actually a Depends, but search.py uses module fn
    # The router calls get_provider directly, not as a dep, so monkeypatch the module fn:
    import app.routers.search as search_module

    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/flights",
            json={
                "origin": "SFO",
                "destination": "HND",
                "depart_date": "2026-10-01",
                "return_date": "2026-10-14",
                "passengers": 1,
                "currency": "USD",
                "max_results": 5,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["provider"] == "fake"
        assert len(body["offers"]) == 3
        assert body["offers"][0]["origin_iata"] == "SFO"
        assert body["offers"][0]["destination_iata"] == "HND"
    finally:
        search_module.get_provider = original
        app.dependency_overrides.pop(get_provider, None)


async def test_search_max_price_filter(authed_client: AsyncClient) -> None:
    import app.routers.search as search_module

    fake = FakeFlightProvider()
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/flights",
            json={
                "origin": "SFO",
                "destination": "HND",
                "depart_date": "2026-10-01",
                "max_price": "525.00",
            },
        )
        assert resp.status_code == 200
        # Fake offers are 500, 550, 600 -> only 500 fits 525 cap.
        assert len(resp.json()["offers"]) == 1
        assert resp.json()["offers"][0]["price"] == "500.00"
    finally:
        search_module.get_provider = original


async def test_save_offer_creates_entry_and_snapshot(authed_client: AsyncClient) -> None:
    holiday = await authed_client.post("/api/holidays", json={"name": "T"})
    holiday_id = holiday.json()["id"]

    save = await authed_client.post(
        "/api/search/save-offer",
        json={
            "holiday_id": holiday_id,
            "offer": {
                "provider": "fake",
                "provider_offer_id": "fake-1",
                "origin_iata": "SFO",
                "destination_iata": "HND",
                "depart_date": "2026-10-01",
                "return_date": "2026-10-14",
                "airline_code": "UA",
                "airline_name": "United",
                "cabin": "ECONOMY",
                "passengers": 1,
                "price": "550.00",
                "currency": "USD",
                "deep_link": "https://example.com/x",
            },
            "raw_payload": {"some": "thing"},
        },
    )
    assert save.status_code == 201, save.text
    entry = save.json()
    assert entry["origin_iata"] == "SFO"
    assert entry["initial_price"] == "550.00"
    assert entry["source"] == "fake"

    snaps = await authed_client.get(
        f"/api/holidays/{holiday_id}/flights/{entry['id']}/snapshots"
    )
    assert snaps.status_code == 200
    assert len(snaps.json()) == 1
