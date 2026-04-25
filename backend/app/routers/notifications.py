from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, update

from app.deps import CurrentUser, DbDep
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, UnreadCountResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: DbDep,
    current_user: CurrentUser,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list((await db.execute(stmt)).scalars().all())


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(db: DbDep, current_user: CurrentUser) -> UnreadCountResponse:
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id, Notification.read_at.is_(None)
        )
    )
    return UnreadCountResponse(unread=int(count or 0))


@router.post("/{notif_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notif_id: int, db: DbDep, current_user: CurrentUser) -> None:
    notif = await db.get(Notification, notif_id)
    if notif is None or notif.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notif.read_at is None:
        notif.read_at = datetime.now(UTC)
        await db.commit()


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(db: DbDep, current_user: CurrentUser) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    await db.commit()
