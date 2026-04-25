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


class FlightProvider(Protocol):
    name: str

    async def search(self, query: SearchQuery) -> list[NormalizedOffer]: ...

    async def reprice(self, stored_payload: dict[str, Any]) -> NormalizedOffer | None: ...


class ProviderError(RuntimeError):
    """Raised when a provider call fails (network, auth, rate limit, etc.)."""
