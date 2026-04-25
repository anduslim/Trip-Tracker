from httpx import AsyncClient


async def _create_holiday(client: AsyncClient) -> int:
    r = await client.post("/api/holidays", json={"name": "Trip", "currency": "USD"})
    assert r.status_code == 201
    return r.json()["id"]


async def test_flight_entry_crud_and_snapshots(authed_client: AsyncClient) -> None:
    holiday_id = await _create_holiday(authed_client)

    create = await authed_client.post(
        f"/api/holidays/{holiday_id}/flights",
        json={
            "origin_iata": "sfo",
            "destination_iata": "hnd",
            "depart_date": "2026-10-01",
            "return_date": "2026-10-14",
            "airline_code": "UA",
            "airline_name": "United",
            "passengers": 1,
            "source_url": "https://example.com/flight",
            "initial_price": "1200.00",
            "currency": "USD",
        },
    )
    assert create.status_code == 201, create.text
    entry = create.json()
    entry_id = entry["id"]
    assert entry["origin_iata"] == "SFO"
    assert entry["destination_iata"] == "HND"
    assert entry["latest_price"] == "1200.00"

    snaps = await authed_client.get(
        f"/api/holidays/{holiday_id}/flights/{entry_id}/snapshots"
    )
    assert snaps.status_code == 200
    assert len(snaps.json()) == 1
    assert snaps.json()[0]["price"] == "1200.00"

    refresh = await authed_client.post(
        f"/api/holidays/{holiday_id}/flights/{entry_id}/refresh",
        json={"price": "1150.00"},
    )
    assert refresh.status_code == 201
    assert refresh.json()["price"] == "1150.00"

    snaps2 = await authed_client.get(
        f"/api/holidays/{holiday_id}/flights/{entry_id}/snapshots"
    )
    assert len(snaps2.json()) == 2

    detail = await authed_client.get(f"/api/holidays/{holiday_id}/flights/{entry_id}")
    assert detail.status_code == 200
    assert detail.json()["latest_price"] == "1150.00"

    patch = await authed_client.patch(
        f"/api/holidays/{holiday_id}/flights/{entry_id}",
        json={"tracking_enabled": False},
    )
    assert patch.status_code == 200
    assert patch.json()["tracking_enabled"] is False

    delete = await authed_client.delete(
        f"/api/holidays/{holiday_id}/flights/{entry_id}"
    )
    assert delete.status_code == 204


async def test_flight_entry_other_user_isolation(client: AsyncClient) -> None:
    # User A
    await client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": "password123"},
    )
    holiday = await client.post("/api/holidays", json={"name": "A trip", "currency": "USD"})
    a_holiday_id = holiday.json()["id"]
    await client.post("/api/auth/logout")

    # User B
    await client.post(
        "/api/auth/register",
        json={"email": "b@example.com", "password": "password123"},
    )
    r = await client.get(f"/api/holidays/{a_holiday_id}")
    assert r.status_code == 404
