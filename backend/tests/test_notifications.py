from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select

from app.models.notification import Notification
from app.models.user import User


async def _seed_notification(db, email: str, *, read: bool = False) -> int:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    n = Notification(
        user_id=user.id,
        type="price_drop",
        title="Test",
        body="Test body",
        email_status="pending",
        read_at=datetime.now(UTC) if read else None,
    )
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n.id


async def test_notifications_listing_and_read(authed_client: AsyncClient, db) -> None:
    n_id = await _seed_notification(db, "u@example.com")
    listing = await authed_client.get("/api/notifications")
    assert listing.status_code == 200
    assert any(n["id"] == n_id for n in listing.json())

    count = await authed_client.get("/api/notifications/unread-count")
    assert count.status_code == 200
    assert count.json()["unread"] >= 1

    mark = await authed_client.post(f"/api/notifications/{n_id}/read")
    assert mark.status_code == 204

    after = await authed_client.get("/api/notifications/unread-count")
    assert after.json()["unread"] == 0


async def test_other_users_notifications_isolated(client: AsyncClient, db) -> None:
    await client.post("/api/auth/register", json={"email": "x@example.com", "password": "password123"})
    await _seed_notification(db, "x@example.com")
    await client.post("/api/auth/logout")

    await client.post("/api/auth/register", json={"email": "y@example.com", "password": "password123"})
    listing = await client.get("/api/notifications")
    assert listing.status_code == 200
    assert listing.json() == []
