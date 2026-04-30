"""Amadeus Self-Service implementation of FlightProvider.

The amadeus SDK is synchronous; we run calls via asyncio.to_thread so
we don't block the event loop. Only used in production / when credentials
are configured. Tests use FakeFlightProvider.
"""
from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from typing import Any

from amadeus import Client, ResponseError

from app.services.flight_provider import (
    FlightProvider,
    MultiCityLeg,
    MultiCityOffer,
    NormalizedOffer,
    PriceAnalysis,
    ProviderError,
    SearchQuery,
)


class AmadeusProvider(FlightProvider):
    name = "amadeus"

    def __init__(self, client_id: str, client_secret: str, hostname: str = "test"):
        self._client = Client(
            client_id=client_id,
            client_secret=client_secret,
            hostname=hostname,
        )

    async def search(self, query: SearchQuery) -> list[NormalizedOffer]:
        params: dict[str, Any] = {
            "originLocationCode": query.origin.upper(),
            "destinationLocationCode": query.destination.upper(),
            "departureDate": query.depart_date.isoformat(),
            "adults": query.passengers,
            "currencyCode": query.currency.upper(),
            "max": query.max_results,
        }
        if query.return_date:
            params["returnDate"] = query.return_date.isoformat()
        if query.cabin:
            params["travelClass"] = query.cabin.upper()
        if query.max_price is not None:
            params["maxPrice"] = int(query.max_price)
        try:
            resp = await asyncio.to_thread(self._client.shopping.flight_offers_search.get, **params)
        except ResponseError as e:
            raise ProviderError(f"Amadeus error: {e}") from e
        return [_to_offer(o) for o in (resp.data or [])]

    async def reprice(self, stored_payload: dict[str, Any]) -> NormalizedOffer | None:
        try:
            resp = await asyncio.to_thread(
                self._client.shopping.flight_offers.pricing.post,
                {"data": {"type": "flight-offers-pricing", "flightOffers": [stored_payload]}},
            )
        except ResponseError:
            return None
        offers = (resp.data or {}).get("flightOffers") or []
        if not offers:
            return None
        return _to_offer(offers[0])

    async def search_multi_city(
        self,
        legs: list[MultiCityLeg],
        *,
        passengers: int = 1,
        cabin: str | None = None,
        currency: str = "USD",
        max_results: int = 10,
    ) -> list[MultiCityOffer]:
        body: dict[str, Any] = {
            "currencyCode": currency.upper(),
            "originDestinations": [
                {
                    "id": str(i + 1),
                    "originLocationCode": leg.origin.upper(),
                    "destinationLocationCode": leg.destination.upper(),
                    "departureDateTimeRange": {"date": leg.depart_date.isoformat()},
                }
                for i, leg in enumerate(legs)
            ],
            "travelers": [
                {"id": str(i + 1), "travelerType": "ADULT"} for i in range(passengers)
            ],
            "sources": ["GDS"],
            "searchCriteria": {"maxFlightOffers": max_results},
        }
        if cabin:
            body["searchCriteria"]["flightFilters"] = {
                "cabinRestrictions": [
                    {
                        "cabin": cabin.upper(),
                        "coverage": "MOST_SEGMENTS",
                        "originDestinationIds": [str(i + 1) for i in range(len(legs))],
                    }
                ]
            }
        try:
            resp = await asyncio.to_thread(
                self._client.shopping.flight_offers_search.post, body
            )
        except ResponseError as e:
            raise ProviderError(f"Amadeus error: {e}") from e

        out: list[MultiCityOffer] = []
        for raw in resp.data or []:
            itineraries = raw.get("itineraries") or []
            if len(itineraries) != len(legs):
                continue
            leg_offers = [_to_offer({**raw, "itineraries": [it]}) for it in itineraries]
            price = raw.get("price", {})
            out.append(
                MultiCityOffer(
                    provider="amadeus",
                    provider_offer_id=str(raw.get("id") or ""),
                    legs=leg_offers,
                    total_price=Decimal(str(price.get("total", "0"))),
                    currency=str(price.get("currency", currency.upper())),
                    raw=raw,
                )
            )
        return out

    async def price_analysis(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        *,
        currency: str = "USD",
        one_way: bool = False,
    ) -> PriceAnalysis | None:
        try:
            resp = await asyncio.to_thread(
                self._client.analytics.itinerary_price_metrics.get,
                originIataCode=origin.upper(),
                destinationIataCode=destination.upper(),
                departureDate=depart_date.isoformat(),
                currencyCode=currency.upper(),
                oneWay="true" if one_way else "false",
            )
        except ResponseError:
            return None
        items = resp.data or []
        if not items:
            return None
        metrics = items[0].get("priceMetrics") or []
        buckets = {m.get("quartileRanking"): Decimal(str(m.get("amount", "0"))) for m in metrics}
        required = ("MINIMUM", "FIRST", "MEDIAN", "THIRD", "MAXIMUM")
        if not all(k in buckets for k in required):
            return None
        return PriceAnalysis(
            origin_iata=origin.upper(),
            destination_iata=destination.upper(),
            depart_date=depart_date,
            currency=currency.upper(),
            minimum=buckets["MINIMUM"],
            first=buckets["FIRST"],
            median=buckets["MEDIAN"],
            third=buckets["THIRD"],
            maximum=buckets["MAXIMUM"],
        )


def _to_offer(raw: dict[str, Any]) -> NormalizedOffer:
    itineraries = raw.get("itineraries") or []
    first_seg = itineraries[0]["segments"][0] if itineraries and itineraries[0].get("segments") else {}
    last_itin = itineraries[-1] if itineraries else {}
    last_seg = last_itin.get("segments", [{}])[-1] if itineraries else {}
    price = raw.get("price", {})
    traveler_pricings = raw.get("travelerPricings") or []
    cabin = None
    if traveler_pricings:
        fare_details = traveler_pricings[0].get("fareDetailsBySegment") or []
        if fare_details:
            cabin = fare_details[0].get("cabin")
    return NormalizedOffer(
        provider="amadeus",
        provider_offer_id=str(raw.get("id") or ""),
        origin_iata=str(first_seg.get("departure", {}).get("iataCode") or ""),
        destination_iata=str(last_seg.get("arrival", {}).get("iataCode") or first_seg.get("arrival", {}).get("iataCode") or ""),
        depart_date=_parse_date(first_seg.get("departure", {}).get("at", "")),
        return_date=_parse_date_or_none(
            itineraries[1]["segments"][0]["departure"]["at"]
            if len(itineraries) > 1 and itineraries[1].get("segments")
            else None
        ),
        airline_code=first_seg.get("carrierCode"),
        airline_name=None,
        cabin=cabin,
        passengers=len(traveler_pricings) or 1,
        price=Decimal(str(price.get("total", "0"))),
        currency=str(price.get("currency", "USD")),
        deep_link=None,
        raw=raw,
    )


def _parse_date(s: str) -> date:
    return date.fromisoformat(s.split("T")[0]) if s else date.min


def _parse_date_or_none(s: str | None) -> date | None:
    if not s:
        return None
    return date.fromisoformat(s.split("T")[0])
