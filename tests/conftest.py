"""Pytest fixtures and configuration."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.services.copilot_service import CopilotService


@pytest.fixture(autouse=True)
def _hermetic_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Force offline/mock settings so tests never depend on a developer's .env or hit a real LLM (T10)."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DECISION_PROVIDER", "mock")
    monkeypatch.setenv("INGESTION_ENABLED", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        LLM_PROVIDER="mock",
        DECISION_PROVIDER="mock",
        DATA_DIR=Path("data"),
        RAW_DATA_DIR=Path("data/raw"),
        STRICT_CITATION_VERIFICATION=True,
    )


@pytest.fixture
def mock_llm() -> MockLLMAdapter:
    return MockLLMAdapter()


@pytest.fixture
def copilot_service(test_settings: Settings, mock_llm: MockLLMAdapter) -> CopilotService:
    return CopilotService(settings=test_settings, llm_client=mock_llm)
