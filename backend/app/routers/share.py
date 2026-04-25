from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbDep
from app.models.holiday import Holiday
from app.schemas.share import ShareTokenResponse
from app.services import share_service

router = APIRouter(prefix="/api/holidays/{holiday_id}/share", tags=["share"])


async def _owned_holiday(db, user_id: int, holiday_id: int) -> Holiday:
    h = (
        await db.execute(
            select(Holiday).where(Holiday.id == holiday_id, Holiday.user_id == user_id)
        )
    ).scalar_one_or_none()
    if h is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return h


def _to_response(token) -> ShareTokenResponse:
    return ShareTokenResponse(
        token=token.token,
        url=share_service.share_url(token.token),
        revoked_at=token.revoked_at,
        expires_at=token.expires_at,
        created_at=token.created_at,
    )


@router.get("", response_model=ShareTokenResponse | None)
async def get_token(holiday_id: int, db: DbDep, current_user: CurrentUser):
    await _owned_holiday(db, current_user.id, holiday_id)
    token = await share_service.get_active_for_holiday(db, holiday_id)
    if token is None:
        return None
    return _to_response(token)


@router.post("", response_model=ShareTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(holiday_id: int, db: DbDep, current_user: CurrentUser) -> ShareTokenResponse:
    await _owned_holiday(db, current_user.id, holiday_id)
    token = await share_service.create_or_rotate(db, holiday_id)
    return _to_response(token)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(holiday_id: int, db: DbDep, current_user: CurrentUser) -> None:
    await _owned_holiday(db, current_user.id, holiday_id)
    await share_service.revoke(db, holiday_id)
