"""Double-submit-cookie CSRF protection.

The middleware does two things on every response: ensures a non-HttpOnly
csrf_token cookie is present (so the SPA can read it), and on unsafe
methods it requires X-CSRF-Token to match the cookie. A cross-origin
attacker can't read the cookie's value (per the same-origin policy), so
they cannot forge a matching header.

`SameSite=Lax` on the auth cookie already blocks most CSRF — this is
defence-in-depth and enforces the contract for non-browser clients
(curl scripts, mobile apps) too.

Skipped paths:
- /api/health, /api/health/*  — used by ops probes
- /api/public/*               — read-only (GET) and rate-limited
"""
from __future__ import annotations

import hmac
import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings

COOKIE_NAME = "csrf_token"
HEADER_NAME = "x-csrf-token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
EXEMPT_PREFIXES = ("/api/public/", "/api/health")


def _new_token() -> str:
    return secrets.token_urlsafe(32)


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_exempt = any(path.startswith(p) for p in EXEMPT_PREFIXES)
        cookie_token = request.cookies.get(COOKIE_NAME)

        if not is_exempt and request.method not in SAFE_METHODS:
            header_token = request.headers.get(HEADER_NAME)
            if (
                not cookie_token
                or not header_token
                or not hmac.compare_digest(cookie_token, header_token)
            ):
                return JSONResponse(
                    {"detail": "CSRF token missing or mismatched"},
                    status_code=403,
                )

        response = await call_next(request)

        if not cookie_token:
            settings = get_settings()
            response.set_cookie(
                key=COOKIE_NAME,
                value=_new_token(),
                httponly=False,
                secure=settings.cookie_secure,
                samesite="lax",
                domain=settings.cookie_domain or None,
                path="/",
                max_age=60 * 60 * 24 * 7,
            )
        return response
