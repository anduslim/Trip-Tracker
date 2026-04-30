"""FlightProvider protocol + a normalized offer shape used by routers and tests.

Concrete providers (Amadeus, SerpApi, Fake) implement `search` and optionally
`reprice`. They never leak provider-specific shapes outward — the router layer
only sees `NormalizedOffer`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Protocol


@dataclass
class SearchQuery:
    origin: str
    destination: str
    depart_date: date
    return_date: date | None = None
    passengers: int = 1
    cabin: str | None = None
    currency: str = "USD"
    max_price: Decimal | None = None
    max_results: int = 20


@dataclass
class NormalizedOffer:
    provider: str
    provider_offer_id: str
    origin_iata: str
    destination_iata: str
    depart_date: date
    return_date: date | None
    airline_code: str | None
    airline_name: str | None
    cabin: str | None
    passengers: int
    price: Decimal
    currency: str
    deep_link: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["depart_date"] = self.depart_date.isoformat()
        d["return_date"] = self.return_date.isoformat() if self.return_date else None
        d["price"] = str(self.price)
        return d


@dataclass
class PriceAnalysis:
    """Quartile-based price context for a route + date.

    Values are inclusive: minimum/first/median/third/maximum bucket boundaries
    matching Amadeus `analytics.itinerary_price_metrics`. A price <= first is
    in the cheapest quartile; > third is in the priciest quartile.
    """
    origin_iata: str
    destination_iata: str
    depart_date: date
    currency: str
    minimum: Decimal
    first: Decimal
    median: Decimal
    third: Decimal
    maximum: Decimal

    def rate(self, price: Decimal) -> str:
        """Classify a price against this analysis. Returns 'cheap', 'good',
        'typical', or 'expensive'."""
        if price <= self.first:
            return "cheap"
        if price <= self.median:
            return "good"
        if price <= self.third:
            return "typical"
        return "expensive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin_iata": self.origin_iata,
            "destination_iata": self.destination_iata,
            "depart_date": self.depart_date.isoformat(),
            "currency": self.currency,
            "minimum": str(self.minimum),
            "first": str(self.first),
            "median": str(self.median),
            "third": str(self.third),
            "maximum": str(self.maximum),
        }


@dataclass
class MultiCityLeg:
    origin: str
    destination: str
    depart_date: date


@dataclass
class MultiCityOffer:
    """A single PNR / ticket covering all legs in order."""
    provider: str
    provider_offer_id: str
    legs: list[NormalizedOffer]
    total_price: Decimal
    currency: str
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_offer_id": self.provider_offer_id,
            "legs": [
                {k: v for k, v in leg.to_dict().items() if k != "raw"}
                for leg in self.legs
            ],
            "total_price": str(self.total_price),
            "currency": self.currency,
        }


class FlightProvider(Protocol):
    name: str

    async def search(self, query: SearchQuery) -> list[NormalizedOffer]: ...

    async def reprice(self, stored_payload: dict[str, Any]) -> NormalizedOffer | None: ...

    async def price_analysis(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        *,
        currency: str = "USD",
        one_way: bool = False,
    ) -> PriceAnalysis | None:
        """Return historical-price quartiles for the route + date, or None
        if the provider doesn't support it."""
        ...

    async def search_multi_city(
        self,
        legs: list[MultiCityLeg],
        *,
        passengers: int = 1,
        cabin: str | None = None,
        currency: str = "USD",
        max_results: int = 10,
    ) -> list[MultiCityOffer]:
        """Find single-PNR itineraries covering all legs in order. Empty
        list when the provider can't service multi-city natively."""
        return []


class ProviderError(RuntimeError):
    """Raised when a provider call fails (network, auth, rate limit, etc.)."""
