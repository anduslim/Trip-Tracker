from httpx import AsyncClient


async def test_register_login_me_logout(client: AsyncClient) -> None:
    r = await client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert "access_token" in r.cookies

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    out = await client.post("/api/auth/logout")
    assert out.status_code == 204

    me2 = await client.get("/api/auth/me")
    assert me2.status_code == 401

    bad = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401

    good = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert good.status_code == 200


async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "password123"}
    r1 = await client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/auth/register", json=payload)
    assert r2.status_code == 409
