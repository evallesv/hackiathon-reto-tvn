"""Background Ingestion Scheduler.

Periodically fetches real data from TVN RSS, GDELT, World Bank, and USGS
and updates the SQLite database mounted on the Fly.io persistent volume.
"""

import asyncio
import logging
from typing import Any

from hackiathon_reto_tvn.adapters.data.live_fetchers import LiveDataFetcher
from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.config import Settings, get_settings

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task[None] | None = None


async def run_ingestion_cycle(settings: Settings | None = None) -> dict[str, Any]:
    """Execute a single ingestion cycle across all live sources."""
    app_settings = settings or get_settings()
    storage = SQLiteStorage(app_settings.SQLITE_DB_PATH)
    fetcher = LiveDataFetcher()
    logger.info(f"Starting live ingestion cycle on SQLite DB: {app_settings.SQLITE_DB_PATH}")
    result = await fetcher.sync_all(storage)
    logger.info(f"Ingestion cycle completed: {result.get('sources')}")
    return result


async def _periodic_worker(interval_seconds: int) -> None:
    """Continuous loop running ingestion cycles at configured intervals."""
    # Wait a few seconds after startup before the first run
    await asyncio.sleep(10)
    while True:
        try:
            logger.info("Executing periodic live data ingestion...")
            await run_ingestion_cycle()
        except asyncio.CancelledError:
            logger.info("Periodic ingestion worker cancelled.")
            break
        except Exception as exc:
            logger.error(f"Error during periodic ingestion: {exc}", exc_info=True)

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


def start_background_scheduler(settings: Settings) -> None:
    """Launch the background ingestion worker if enabled."""
    global _scheduler_task
    if not settings.INGESTION_ENABLED or settings.ENVIRONMENT == "test":
        logger.info("Periodic ingestion is disabled by configuration or in test mode.")
        return

    interval_secs = max(60, settings.INGESTION_INTERVAL_MINUTES * 60)
    logger.info(f"Scheduling periodic ingestion every {settings.INGESTION_INTERVAL_MINUTES} minutes ({interval_secs}s)")
    loop = asyncio.get_event_loop()
    _scheduler_task = loop.create_task(_periodic_worker(interval_secs))


def stop_background_scheduler() -> None:
    """Cancel the background ingestion worker if running."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        logger.info("Stopping periodic ingestion background task...")
        _scheduler_task.cancel()
        _scheduler_task = None
