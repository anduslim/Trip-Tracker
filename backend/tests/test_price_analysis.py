from datetime import date
from decimal import Decimal

from httpx import AsyncClient

import app.routers.search as search_module
from app.services.fake_provider import FakeFlightProvider
from app.services.flight_provider import PriceAnalysis


def test_rate_classifies_against_quartiles() -> None:
    pa = PriceAnalysis(
        origin_iata="SFO",
        destination_iata="HND",
        depart_date=date(2026, 10, 1),
        currency="USD",
        minimum=Decimal("400"),
        first=Decimal("525"),
        median=Decimal("600"),
        third=Decimal("700"),
        maximum=Decimal("900"),
    )
    assert pa.rate(Decimal("400")) == "cheap"
    assert pa.rate(Decimal("525")) == "cheap"
    assert pa.rate(Decimal("550")) == "good"
    assert pa.rate(Decimal("600")) == "good"
    assert pa.rate(Decimal("650")) == "typical"
    assert pa.rate(Decimal("700")) == "typical"
    assert pa.rate(Decimal("701")) == "expensive"


async def test_search_includes_price_analysis(authed_client: AsyncClient) -> None:
    fake = FakeFlightProvider()  # default analysis: q1=525, median=600, q3=700
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/flights",
            json={
                "origin": "SFO",
                "destination": "HND",
                "depart_date": "2026-10-01",
                "currency": "USD",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["price_analysis"] is not None
        assert body["price_analysis"]["median"] == "600"

        # Default fake offers cost 500, 550, 600. Ratings:
        #   500 <= 525 → cheap
        #   550 in (525, 600] → good
        #   600 in (525, 600] → good
        ratings = [o["price_rating"] for o in body["offers"]]
        assert ratings == ["cheap", "good", "good"]

        # Analysis was actually called.
        assert fake.analysis_calls == [("SFO", "HND", "2026-10-01")]
    finally:
        search_module.get_provider = original


async def test_search_handles_no_analysis(authed_client: AsyncClient) -> None:
    """If the provider has no analysis (e.g. SerpApi), search still works
    and offers have no rating."""
    fake = FakeFlightProvider()
    fake._analysis = None  # type: ignore[assignment]

    async def no_analysis(*args, **kwargs):
        return None

    fake.price_analysis = no_analysis  # type: ignore[assignment]
    original = search_module.get_provider
    search_module.get_provider = lambda name=None: fake  # type: ignore[assignment]
    try:
        resp = await authed_client.post(
            "/api/search/flights",
            json={
                "origin": "SFO",
                "destination": "HND",
                "depart_date": "2026-10-01",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["price_analysis"] is None
        assert all(o["price_rating"] is None for o in body["offers"])
    finally:
        search_module.get_provider = original
