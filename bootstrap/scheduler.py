from functools import partial
from logging import Logger

from fastapi import FastAPI

from apps.users.service import UserService
from core.db import SessionLocal
from infrastructure.scheduler.base import BaseScheduler


async def _cleanup_unverified_users(logger: Logger) -> None:
    """Scheduled job: delete users left unverified past the retention window."""
    async with SessionLocal() as session:
        deleted = await UserService(session).cleanup_unverified()
    if deleted:
        logger.info("Cleanup: removed %s unverified user(s)", deleted)


def setup_schedulers(app: FastAPI, logger: Logger) -> None:
    """Start background jobs (auto-remove unverified users)."""
    scheduler = BaseScheduler(logger=logger)
    scheduler.add_cron_job(
        job_id="cleanup_unverified_users",
        func=partial(_cleanup_unverified_users, logger),
        # Runs hourly; the retention threshold itself is 2 days.
        minute=0,
    )
    scheduler.start()
    app.state.scheduler = scheduler


def shutdown_schedulers(app: FastAPI, logger: Logger) -> None:
    """Stop background jobs on application shutdown."""
    scheduler: BaseScheduler | None = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown()
