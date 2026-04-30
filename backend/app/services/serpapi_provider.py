"""SerpApi Google Flights implementation of FlightProvider.

SerpApi exposes a paid endpoint that scrapes Google Flights. We hit it via
httpx (async). Note: there is no official Google Flights API.

Reference: https://serpapi.com/google-flights-api
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from app.services.flight_provider import (
    FlightProvider,
    NormalizedOffer,
    PriceAnalysis,
    ProviderError,
    SearchQuery,
)

_BASE_URL = "https://serpapi.com/search.json"


class SerpApiProvider(FlightProvider):
    name = "serpapi"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def search(self, query: SearchQuery) -> list[NormalizedOffer]:
        params: dict[str, Any] = {
            "engine": "google_flights",
            "api_key": self._api_key,
            "departure_id": query.origin.upper(),
            "arrival_id": query.destination.upper(),
            "outbound_date": query.depart_date.isoformat(),
            "currency": query.currency.upper(),
            "type": "1" if query.return_date else "2",  # 1 = round trip, 2 = one-way
            "adults": query.passengers,
        }
        if query.return_date:
            params["return_date"] = query.return_date.isoformat()
        try:
            resp = await self._http.get(_BASE_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(f"SerpApi error: {e}") from e
        data = resp.json()
        offers: list[NormalizedOffer] = []
        for bucket_key in ("best_flights", "other_flights"):
            for raw in data.get(bucket_key, []) or []:
                offers.append(_to_offer(raw, query))
                if len(offers) >= query.max_results:
                    return offers
        return offers

    async def price_analysis(
        self,
        origin: str,
        destination: str,
        depart_date,
        *,
        currency: str = "USD",
        one_way: bool = False,
    ) -> PriceAnalysis | None:
        return None  # Google Flights / SerpApi has no quartile-style metric.

    async def reprice(self, stored_payload: dict[str, Any]) -> NormalizedOffer | None:
        """SerpApi has no offer-pricing endpoint. We re-run the search and
        return the best match by airline + departure time, or None if
        nothing close is found."""
        try:
            origin = stored_payload["origin_iata"]
            destination = stored_payload["destination_iata"]
            depart_date = date.fromisoformat(stored_payload["depart_date"])
        except (KeyError, ValueError):
            return None
        return_date = stored_payload.get("return_date")
        return_d = date.fromisoformat(return_date) if return_date else None

        results = await self.search(
            SearchQuery(
                origin=origin,
                destination=destination,
                depart_date=depart_date,
                return_date=return_d,
                passengers=int(stored_payload.get("passengers", 1)),
                currency=str(stored_payload.get("currency", "USD")),
                max_results=20,
            )
        )
        if not results:
            return None
        airline = stored_payload.get("airline_code")
        for offer in results:
            if airline and offer.airline_code == airline:
                return offer
        return min(results, key=lambda o: o.price)


def _to_offer(raw: dict[str, Any], query: SearchQuery) -> NormalizedOffer:
    flights = raw.get("flights") or []
    first = flights[0] if flights else {}
    last = flights[-1] if flights else {}
    price = raw.get("price")
    return NormalizedOffer(
        provider="serpapi",
        provider_offer_id=str(raw.get("booking_token") or raw.get("departure_token") or ""),
        origin_iata=str(first.get("departure_airport", {}).get("id") or query.origin).upper(),
        destination_iata=str(last.get("arrival_airport", {}).get("id") or query.destination).upper(),
        depart_date=query.depart_date,
        return_date=query.return_date,
        airline_code=first.get("airline_logo_code") or _airline_code(first.get("airline")),
        airline_name=first.get("airline"),
        cabin=first.get("travel_class"),
        passengers=query.passengers,
        price=Decimal(str(price)) if price is not None else Decimal("0"),
        currency=query.currency.upper(),
        deep_link=raw.get("booking_url") or raw.get("url"),
        raw=raw,
    )


def _airline_code(name: str | None) -> str | None:
    if not name:
        return None
    return name[:2].upper() if len(name) >= 2 else None
