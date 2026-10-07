"""Application configuration and settings management via pydantic-settings.

Supports environment variables and .env files with interchangeable LLM providers:
- opencode (Default: model muse-spark-1.3-contributor-free)
- gemini (Alternative: model gemini-2.5-flash / gemini-1.5-flash)
- mock (Offline testing and CI fallback)
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for HackIAthon Copilot."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Environment
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # LLM Provider Selection (Generative System Two)
    LLM_PROVIDER: Literal["opencode", "gemini", "mock"] = "opencode"

    # Decision Model Provider Selection (System One Classification)
    DECISION_PROVIDER: Literal["cloudflare", "jev", "mock"] = "cloudflare"
    DECISION_CONCURRENCY_LIMIT: int = Field(
        default=5,
        description="Límite máximo de peticiones concurrentes al modelo de decisión",
    )

    # Cloudflare Clef Settings (Default Decision Model)
    CLOUDFLARE_ACCOUNT_ID: str = Field(default="", description="Cloudflare Account ID")
    CLOUDFLARE_API_TOKEN: str = Field(default="", description="API Token para Cloudflare Workers AI")
    CLOUDFLARE_DECISION_MODEL: str = Field(
        default="@cf/cloudflare/clef",
        description="Modelo de decisión de Cloudflare (@cf/cloudflare/clef o @cf/cloudflare/clef-flash)",
    )
    CLOUDFLARE_TIMEOUT_SECONDS: float = 30.0

    # TypeSafe Jev Settings (Alternative Commercial Decision Model)
    TYPESAFE_API_KEY: str = Field(default="", description="API Key para TypeSafe Jev API")
    TYPESAFE_BASE_URL: str = Field(
        default="https://api.typesafe.ai/v1/systemone",
        description="Endpoint base de TypeSafe Jev System One",
    )
    TYPESAFE_MODEL: str = Field(
        default="jev-latest",
        description="Identificador del modelo Jev",
    )
    TYPESAFE_TIMEOUT_SECONDS: float = 30.0

    # OpenCode Settings (Default Provider)
    OPENCODE_API_KEY: str = Field(default="", description="API Key for OpenCode")
    OPENCODE_BASE_URL: str = Field(
        default="https://api.opencode.ai/v1",
        description="Base URL for OpenCode OpenAI-compatible API",
    )
    OPENCODE_MODEL: str = Field(
        default="muse-spark-1.3-contributor-free",
        description="Default OpenCode model per hackathon requirement",
    )
    OPENCODE_TIMEOUT_SECONDS: float = 45.0

    # Google Gemini Settings (Alternative Provider)
    GEMINI_API_KEY: str = Field(default="", description="API Key for Google GenAI / Gemini")
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier",
    )
    GEMINI_TIMEOUT_SECONDS: float = 45.0

    # Data Paths
    DATA_DIR: Path = Path("data")
    RAW_DATA_DIR: Path = Path("data/raw")
    PROCESSED_DATA_DIR: Path = Path("data/processed")
    BENCHMARK_PATH: Path = Path("data/benchmark.jsonl")
    MANIFEST_PATH: Path = Path("data/manifest.json")

    # Notion Integration
    NOTION_API_KEY: str = ""
    NOTION_DATABASE_ID: str = ""

    # Editorial Constraints
    MAX_SUMMARY_WORDS_TVN_BRIEF: int = 250
    MAX_WORDS_TVN_DIGITAL_COPY: int = 80
    SCRIPT_DURATION_SECONDS_MIN: int = 45
    SCRIPT_DURATION_SECONDS_MAX: int = 60
    STRICT_CITATION_VERIFICATION: bool = True
    PROMPT_INJECTION_SHIELD_ENABLED: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
