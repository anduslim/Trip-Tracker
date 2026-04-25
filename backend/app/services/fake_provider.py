"""Fake provider for tests and dev when no real credentials are configured."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from app.services.flight_provider import (
    FlightProvider,
    NormalizedOffer,
    SearchQuery,
)


class FakeFlightProvider(FlightProvider):
    name = "fake"

    def __init__(
        self,
        *,
        offers: list[NormalizedOffer] | None = None,
        reprice_value: Decimal | None = None,
    ):
        self._offers = offers
        self._reprice_value = reprice_value
        self.search_calls: list[SearchQuery] = []
        self.reprice_calls: list[dict[str, Any]] = []

    async def search(self, query: SearchQuery) -> list[NormalizedOffer]:
        self.search_calls.append(query)
        if self._offers is not None:
            return self._offers
        # Generate three deterministic offers around the requested route/date.
        base = Decimal("500.00")
        return [
            NormalizedOffer(
                provider="fake",
                provider_offer_id=f"fake-{i}",
                origin_iata=query.origin.upper(),
                destination_iata=query.destination.upper(),
                depart_date=query.depart_date,
                return_date=query.return_date,
                airline_code=["UA", "AA", "DL"][i],
                airline_name=["United", "American", "Delta"][i],
                cabin=query.cabin or "ECONOMY",
                passengers=query.passengers,
                price=base + Decimal(i * 50),
                currency=query.currency.upper(),
                deep_link=f"https://example.com/fake/{i}",
                raw={"offer_index": i, "depart": query.depart_date.isoformat()},
            )
            for i in range(3)
        ]

    async def reprice(self, stored_payload: dict[str, Any]) -> NormalizedOffer | None:
        self.reprice_calls.append(stored_payload)
        if self._reprice_value is None:
            return None
        depart = stored_payload.get("depart_date")
        from datetime import date

        depart_d = date.fromisoformat(depart) if isinstance(depart, str) else date.today() + timedelta(days=30)
        return NormalizedOffer(
            provider="fake",
            provider_offer_id=str(stored_payload.get("provider_offer_id") or "fake-reprice"),
            origin_iata=str(stored_payload.get("origin_iata", "")),
            destination_iata=str(stored_payload.get("destination_iata", "")),
            depart_date=depart_d,
            return_date=None,
            airline_code=stored_payload.get("airline_code"),
            airline_name=stored_payload.get("airline_name"),
            cabin=stored_payload.get("cabin"),
            passengers=int(stored_payload.get("passengers", 1)),
            price=self._reprice_value,
            currency=str(stored_payload.get("currency", "USD")),
            deep_link=None,
            raw={},
        )
