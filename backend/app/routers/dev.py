"""Developer-only utilities. Mounted only when DEBUG is true."""
from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.db import SessionLocal
from app.deps import CurrentUser
from app.services.price_tracker import (
    dispatch_pending_emails,
    prune_old_snapshots,
    refresh_due_entries,
)

router = APIRouter(prefix="/api/dev", tags=["dev"])


def _gate() -> None:
    if not get_settings().debug:
        raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.post("/refresh")
async def manual_refresh(_user: CurrentUser) -> dict[str, int]:
    _gate()
    n = await refresh_due_entries(SessionLocal)
    return {"refreshed": n}


@router.post("/dispatch-emails")
async def manual_dispatch(_user: CurrentUser) -> dict[str, int]:
    _gate()
    n = await dispatch_pending_emails(SessionLocal)
    return {"sent": n}


@router.post("/prune-snapshots")
async def manual_prune(_user: CurrentUser) -> dict[str, int]:
    _gate()
    n = await prune_old_snapshots(SessionLocal)
    return {"deleted": n}
