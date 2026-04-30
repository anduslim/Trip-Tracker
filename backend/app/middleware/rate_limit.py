"""Simple in-memory rate limiter for the public read-only endpoints.

Bucket: requests-per-minute keyed by client IP. Designed for a single-process
deployment; if we ever scale beyond one container, swap for a Redis-backed
limiter (e.g. slowapi or limits)."""
from __future__ import annotations

import time
from collections import deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


# Module-level bucket store. Single dict so tests can reset between cases
# without reaching into middleware internals.
_BUCKETS: dict[str, deque[float]] = {}


def reset_buckets() -> None:
    """Clear all rate-limit state. Test-only."""
    _BUCKETS.clear()


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, prefix: str = "/api/public/"):
        super().__init__(app)
        self._prefix = prefix
        self._buckets = _BUCKETS

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self._prefix):
            return await call_next(request)

        settings = get_settings()
        limit = settings.rate_limit_public_per_minute
        window = 60.0
        now = time.monotonic()
        key = (request.client.host if request.client else "anon")
        bucket = self._buckets.setdefault(key, deque())
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = int(window - (now - bucket[0])) + 1
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
        return await call_next(request)
