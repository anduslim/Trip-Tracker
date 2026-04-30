"""APScheduler wiring. Started/stopped from FastAPI's lifespan."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.services.price_tracker import (
    dispatch_pending_emails,
    prune_old_snapshots,
    refresh_due_entries,
)

log = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled:
        log.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return None
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _refresh_job,
        IntervalTrigger(minutes=settings.price_refresh_interval_minutes),
        id="refresh_tracked_prices",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        _email_job,
        IntervalTrigger(minutes=1),
        id="dispatch_email_queue",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        _prune_job,
        CronTrigger(hour=3, minute=0),
        id="prune_old_snapshots",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    log.info("Scheduler started.")
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _refresh_job() -> None:
    try:
        n = await refresh_due_entries(SessionLocal)
        log.info("refresh_tracked_prices: %d entries refreshed", n)
    except Exception:
        log.exception("refresh_tracked_prices failed")


async def _email_job() -> None:
    try:
        n = await dispatch_pending_emails(SessionLocal)
        if n:
            log.info("dispatch_email_queue: sent %d", n)
    except Exception:
        log.exception("dispatch_email_queue failed")


async def _prune_job() -> None:
    try:
        n = await prune_old_snapshots(SessionLocal)
        if n:
            log.info("prune_old_snapshots: deleted %d rows", n)
    except Exception:
        log.exception("prune_old_snapshots failed")
