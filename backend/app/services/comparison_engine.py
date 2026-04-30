"""Pure-function comparison engine over a holiday's flight entries.

Returns route groupings + insights (cheapest route, biggest 30d drop,
average price per route). Snapshots are loaded by the caller and passed
in keyed by entry_id to keep this module side-effect free and easy to test.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.models.flight_entry import FlightEntry
from app.models.price_snapshot import PriceSnapshot


@dataclass
class RouteGroup:
    origin: str
    destination: str
    entry_count: int
    min_price: Decimal
    avg_price: Decimal
    max_price: Decimal
    cheapest_entry_id: int


@dataclass
class Insights:
    cheapest_route: dict[str, Any] | None
    biggest_drop_30d: dict[str, Any] | None
    avg_price_per_route: list[dict[str, Any]]
    best_day_of_week: list[dict[str, Any]]


@dataclass
class ComparisonResult:
    route_groups: list[RouteGroup]
    insights: Insights

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_groups": [
                {**asdict(g), "min_price": str(g.min_price), "avg_price": str(g.avg_price), "max_price": str(g.max_price)}
                for g in self.route_groups
            ],
            "insights": asdict(self.insights),
        }


def _avg(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    total = sum(values, Decimal("0"))
    return (total / len(values)).quantize(Decimal("0.01"))


def build_comparison(
    entries: list[FlightEntry],
    snapshots_by_entry: dict[int, list[PriceSnapshot]],
) -> ComparisonResult:
    if not entries:
        return ComparisonResult(
            route_groups=[],
            insights=Insights(
                cheapest_route=None,
                biggest_drop_30d=None,
                avg_price_per_route=[],
                best_day_of_week=[],
            ),
        )

    by_route: dict[tuple[str, str], list[FlightEntry]] = defaultdict(list)
    for e in entries:
        by_route[(e.origin_iata, e.destination_iata)].append(e)

    groups: list[RouteGroup] = []
    for (origin, destination), bucket in by_route.items():
        prices = [Decimal(str(b.latest_price)) for b in bucket]
        cheapest = min(bucket, key=lambda b: Decimal(str(b.latest_price)))
        groups.append(
            RouteGroup(
                origin=origin,
                destination=destination,
                entry_count=len(bucket),
                min_price=min(prices),
                avg_price=_avg(prices),
                max_price=max(prices),
                cheapest_entry_id=cheapest.id,
            )
        )

    cheapest_group = min(groups, key=lambda g: g.min_price)
    cheapest_entry = next(e for e in entries if e.id == cheapest_group.cheapest_entry_id)

    cutoff = datetime.now(UTC) - timedelta(days=30)
    biggest_drop: tuple[FlightEntry, Decimal, float] | None = None
    for entry in entries:
        snaps = snapshots_by_entry.get(entry.id) or []
        recent = [s for s in snaps if s.captured_at and _ensure_utc(s.captured_at) >= cutoff]
        if len(recent) < 2:
            continue
        recent_sorted = sorted(recent, key=lambda s: _ensure_utc(s.captured_at))
        first = Decimal(str(recent_sorted[0].price))
        last = Decimal(str(recent_sorted[-1].price))
        if first == 0:
            continue
        delta = last - first
        if delta >= 0:
            continue
        delta_pct = float(delta / first * 100)
        if biggest_drop is None or delta_pct < biggest_drop[2]:
            biggest_drop = (entry, delta, delta_pct)

    biggest_drop_dict = None
    if biggest_drop is not None:
        e, delta, pct = biggest_drop
        biggest_drop_dict = {
            "flight_entry_id": e.id,
            "origin": e.origin_iata,
            "destination": e.destination_iata,
            "delta": str(delta),
            "delta_pct": pct,
            "currency": e.currency,
        }

    best_dow = _best_day_of_week(by_route)

    insights = Insights(
        cheapest_route={
            "origin": cheapest_group.origin,
            "destination": cheapest_group.destination,
            "price": str(cheapest_entry.latest_price),
            "currency": cheapest_entry.currency,
            "flight_entry_id": cheapest_entry.id,
        },
        biggest_drop_30d=biggest_drop_dict,
        avg_price_per_route=[
            {
                "origin": g.origin,
                "destination": g.destination,
                "avg_price": str(g.avg_price),
                "entry_count": g.entry_count,
            }
            for g in sorted(groups, key=lambda g: g.avg_price)
        ],
        best_day_of_week=best_dow,
    )
    return ComparisonResult(route_groups=groups, insights=insights)


_DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _best_day_of_week(by_route: dict[tuple[str, str], list[FlightEntry]]) -> list[dict[str, Any]]:
    """For each route, average the latest_price grouped by depart-date weekday.
    Only emit when we've seen at least 4 distinct weekdays for the route —
    otherwise the result is misleading."""
    out: list[dict[str, Any]] = []
    for (origin, destination), bucket in by_route.items():
        by_dow: dict[int, list[Decimal]] = {}
        for e in bucket:
            by_dow.setdefault(e.depart_date.weekday(), []).append(Decimal(str(e.latest_price)))
        if len(by_dow) < 4:
            continue
        averages = [(dow, _avg(prices)) for dow, prices in by_dow.items()]
        best_dow, best_avg = min(averages, key=lambda x: x[1])
        out.append(
            {
                "origin": origin,
                "destination": destination,
                "best_day": _DOW_NAMES[best_dow],
                "avg_price": str(best_avg),
                "samples": sum(len(v) for v in by_dow.values()),
            }
        )
    return out


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
