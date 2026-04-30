"""Share token lifecycle: generate, rotate, revoke, resolve."""
from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.holiday import Holiday
from app.models.share_token import ShareToken


class ShareTokenInvalid(Exception):
    """Raised when a token is unknown, revoked, or expired."""


def _new_token() -> str:
    return secrets.token_urlsafe(32)


async def get_active_for_holiday(db: AsyncSession, holiday_id: int) -> ShareToken | None:
    return (
        await db.execute(
            select(ShareToken).where(
                ShareToken.holiday_id == holiday_id, ShareToken.revoked_at.is_(None)
            )
        )
    ).scalar_one_or_none()


async def create_or_rotate(db: AsyncSession, holiday_id: int) -> ShareToken:
    """Generate a fresh token. Any existing token row for this holiday is
    hard-deleted — once we rotate, the old random token is worthless and we
    save space by not keeping revoked rows around."""
    existing = (
        await db.execute(
            select(ShareToken).where(ShareToken.holiday_id == holiday_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        await db.flush()
    token = ShareToken(holiday_id=holiday_id, token=_new_token())
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def revoke(db: AsyncSession, holiday_id: int) -> None:
    existing = await get_active_for_holiday(db, holiday_id)
    if existing is not None:
        existing.revoked_at = datetime.now(UTC)
        await db.commit()


async def resolve(db: AsyncSession, token: str) -> Holiday:
    row = (
        await db.execute(select(ShareToken).where(ShareToken.token == token))
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        raise ShareTokenInvalid()
    if row.expires_at is not None and row.expires_at < datetime.now(UTC):
        raise ShareTokenInvalid()
    holiday = await db.get(Holiday, row.holiday_id)
    if holiday is None:
        raise ShareTokenInvalid()
    return holiday


def share_url(token: str) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/share/{token}"
