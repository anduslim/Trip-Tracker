from httpx import AsyncClient


async def _make_holiday(client: AsyncClient) -> int:
    r = await client.post("/api/holidays", json={"name": "Trip"})
    return r.json()["id"]


async def test_share_token_lifecycle(authed_client: AsyncClient) -> None:
    holiday_id = await _make_holiday(authed_client)

    # No token initially
    r = await authed_client.get(f"/api/holidays/{holiday_id}/share")
    assert r.status_code == 200
    assert r.json() is None

    # Create
    create = await authed_client.post(f"/api/holidays/{holiday_id}/share")
    assert create.status_code == 201
    token = create.json()["token"]
    assert len(token) >= 32
    assert create.json()["url"].endswith(f"/share/{token}")

    # Public view works
    pub = await authed_client.get(f"/api/public/share/{token}")
    assert pub.status_code == 200
    assert pub.json()["holiday"]["name"] == "Trip"

    # Rotate
    rotated = await authed_client.post(f"/api/holidays/{holiday_id}/share")
    new_token = rotated.json()["token"]
    assert new_token != token

    # Old token now revoked -> 410
    old = await authed_client.get(f"/api/public/share/{token}")
    assert old.status_code == 410

    # Revoke
    rev = await authed_client.delete(f"/api/holidays/{holiday_id}/share")
    assert rev.status_code == 204
    after = await authed_client.get(f"/api/public/share/{new_token}")
    assert after.status_code == 410


async def test_other_user_cannot_create_token(client: AsyncClient) -> None:
    await client.post("/api/auth/register", json={"email": "owner@example.com", "password": "password123"})
    holiday_id = await _make_holiday(client)
    await client.post("/api/auth/logout")

    await client.post("/api/auth/register", json={"email": "thief@example.com", "password": "password123"})
    r = await client.post(f"/api/holidays/{holiday_id}/share")
    assert r.status_code == 404


async def test_unknown_token_returns_410(client: AsyncClient) -> None:
    r = await client.get("/api/public/share/does-not-exist")
    assert r.status_code == 410
