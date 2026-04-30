from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.main import app


@pytest_asyncio.fixture
async def raw_client(session_factory, _patch_session_local) -> AsyncIterator[AsyncClient]:
    """A client that does NOT auto-inject X-CSRF-Token, used to verify the
    middleware's enforcement directly."""
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


async def test_csrf_blocks_post_without_header(raw_client: AsyncClient) -> None:
    # Prime the cookie with a safe GET first.
    await raw_client.get("/api/health")
    assert "csrf_token" in raw_client.cookies
    # Mutating request without the header → 403.
    r = await raw_client.post(
        "/api/auth/register",
        json={"email": "a@a.com", "password": "password123"},
    )
    assert r.status_code == 403
    assert "CSRF" in r.json()["detail"]


async def test_csrf_blocks_mismatched_header(raw_client: AsyncClient) -> None:
    await raw_client.get("/api/health")
    r = await raw_client.post(
        "/api/auth/register",
        json={"email": "b@b.com", "password": "password123"},
        headers={"X-CSRF-Token": "this-does-not-match"},
    )
    assert r.status_code == 403


async def test_csrf_allows_post_with_matching_header(raw_client: AsyncClient) -> None:
    await raw_client.get("/api/health")
    token = raw_client.cookies.get("csrf_token")
    assert token
    r = await raw_client.post(
        "/api/auth/register",
        json={"email": "c@c.com", "password": "password123"},
        headers={"X-CSRF-Token": token},
    )
    assert r.status_code == 201, r.text


async def test_public_endpoints_exempt(raw_client: AsyncClient) -> None:
    # /api/public/* methods are read-only (GET) anyway, but verify exemption
    # by checking a GET works without the cookie.
    r = await raw_client.get("/api/public/share/does-not-exist")
    assert r.status_code in {410, 429}  # 429 only if previous tests hit rate limit


async def test_safe_methods_skip_check(raw_client: AsyncClient) -> None:
    # GET /api/auth/me without auth returns 401, not 403 from CSRF.
    r = await raw_client.get("/api/auth/me")
    assert r.status_code == 401
