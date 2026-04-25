"""Provider registry. Builds the configured providers lazily.

In tests, callers override `app.dependency_overrides[get_provider]`.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.services.fake_provider import FakeFlightProvider
from app.services.flight_provider import FlightProvider


@lru_cache
def _build_amadeus(settings: Settings) -> FlightProvider | None:
    if not (settings.amadeus_client_id and settings.amadeus_client_secret):
        return None
    from app.services.amadeus_provider import AmadeusProvider

    return AmadeusProvider(
        client_id=settings.amadeus_client_id,
        client_secret=settings.amadeus_client_secret,
        hostname=settings.amadeus_hostname,
    )


@lru_cache
def _build_serpapi(settings: Settings) -> FlightProvider | None:
    if not settings.serpapi_key:
        return None
    from app.services.serpapi_provider import SerpApiProvider

    return SerpApiProvider(api_key=settings.serpapi_key)


def available_providers(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    out: list[str] = []
    if _build_amadeus(settings):
        out.append("amadeus")
    if _build_serpapi(settings):
        out.append("serpapi")
    if not out:
        out.append("fake")
    return out


def get_provider(name: str | None = None, settings: Settings | None = None) -> FlightProvider:
    """Resolve a provider by name. Falls back to FakeFlightProvider when none
    are configured (useful for local dev without credentials)."""
    settings = settings or get_settings()
    requested = (name or settings.default_flight_provider or "amadeus").lower()
    if requested == "amadeus":
        prov = _build_amadeus(settings)
        if prov:
            return prov
    if requested == "serpapi":
        prov = _build_serpapi(settings)
        if prov:
            return prov
    if requested == "fake":
        return FakeFlightProvider()
    # Auto-fallback chain.
    for fn in (_build_amadeus, _build_serpapi):
        prov = fn(settings)
        if prov:
            return prov
    return FakeFlightProvider()
