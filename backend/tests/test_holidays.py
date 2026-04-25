from httpx import AsyncClient


async def test_holiday_crud(authed_client: AsyncClient) -> None:
    create = await authed_client.post(
        "/api/holidays",
        json={
            "name": "Japan 2026",
            "start_date": "2026-10-01",
            "end_date": "2026-10-14",
            "destinations": [{"city": "Tokyo", "iata": "HND", "country": "JP"}],
            "currency": "USD",
        },
    )
    assert create.status_code == 201, create.text
    holiday = create.json()
    holiday_id = holiday["id"]
    assert holiday["name"] == "Japan 2026"

    listing = await authed_client.get("/api/holidays")
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["flight_entry_count"] == 0

    detail = await authed_client.get(f"/api/holidays/{holiday_id}")
    assert detail.status_code == 200
    assert detail.json()["flight_entries"] == []

    patch = await authed_client.patch(
        f"/api/holidays/{holiday_id}", json={"notes": "Updated"}
    )
    assert patch.status_code == 200
    assert patch.json()["notes"] == "Updated"

    delete = await authed_client.delete(f"/api/holidays/{holiday_id}")
    assert delete.status_code == 204

    listing2 = await authed_client.get("/api/holidays")
    assert listing2.json() == []


async def test_holidays_require_auth(client: AsyncClient) -> None:
    r = await client.get("/api/holidays")
    assert r.status_code == 401
