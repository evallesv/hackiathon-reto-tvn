"""Factory for interchangeable LLM providers (OpenCode, Gemini, Mock)."""

import logging
from typing import Optional

from hackiathon_reto_tvn.adapters.llm.gemini_adapter import GeminiAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.adapters.llm.opencode_adapter import OpenCodeAdapter
from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.ports.llm_port import BaseLLMClient

logger = logging.getLogger(__name__)


def get_llm_client(settings: Optional[Settings] = None) -> BaseLLMClient:
    """Factory creating the configured LLM client.

    Default: OpenCode with muse-spark-1.3-contributor-free
    Alternative: Gemini
    Offline / testing: Mock
    """
    cfg = settings or get_settings()

    if cfg.LLM_PROVIDER == "opencode":
        logger.info(f"Using OpenCode LLM client with model '{cfg.OPENCODE_MODEL}' at {cfg.OPENCODE_BASE_URL}")
        return OpenCodeAdapter(
            api_key=cfg.OPENCODE_API_KEY,
            base_url=cfg.OPENCODE_BASE_URL,
            model=cfg.OPENCODE_MODEL,
            timeout=cfg.OPENCODE_TIMEOUT_SECONDS,
        )

    elif cfg.LLM_PROVIDER == "gemini":
        logger.info(f"Using Google Gemini LLM client with model '{cfg.GEMINI_MODEL}'")
        return GeminiAdapter(
            api_key=cfg.GEMINI_API_KEY,
            model=cfg.GEMINI_MODEL,
            timeout=cfg.GEMINI_TIMEOUT_SECONDS,
        )

    elif cfg.LLM_PROVIDER == "mock":
        logger.info("Using Mock LLM client (offline deterministic mode)")
        return MockLLMAdapter(model_name="mock-muse-spark-offline")

    else:
        logger.warning(f"Unknown LLM provider '{cfg.LLM_PROVIDER}', falling back to Mock provider")
        return MockLLMAdapter()
