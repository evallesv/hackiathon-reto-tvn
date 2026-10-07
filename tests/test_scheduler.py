"""Tests for the background ingestion scheduler."""

from unittest.mock import AsyncMock, patch

import pytest

from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.services.ingestion_scheduler import (
    run_ingestion_cycle,
    start_background_scheduler,
    stop_background_scheduler,
)


@pytest.mark.asyncio
async def test_run_ingestion_cycle_calls_fetcher(tmp_path) -> None:
    test_settings = Settings(
        ENVIRONMENT="test",
        SQLITE_DB_PATH=tmp_path / "sched_test.db",
        INGESTION_ENABLED=False,
    )
    with patch(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.LiveDataFetcher.sync_all",
        new_callable=AsyncMock,
        return_value={"status": "mock_ok", "sources": {}},
    ) as mock_sync:
        result = await run_ingestion_cycle(test_settings)
        assert result["status"] == "mock_ok"
        mock_sync.assert_called_once()


def test_scheduler_start_stop() -> None:
    settings = Settings(
        ENVIRONMENT="test",
        INGESTION_ENABLED=False,
    )
    # Disabled in test mode: should not raise
    start_background_scheduler(settings)
    stop_background_scheduler()
