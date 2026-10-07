"""LLM Port specification using clean architecture / hexagonal pattern.

Defines the contract for interchangeable LLM connectors:
- OpenCode (Default: muse-spark-1.3-contributor-free)
- Google Gemini (Alternative: gemini-2.5-flash)
- Mock (Deterministic testing & offline fallback)
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract interface for LLM connectors."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider name (e.g., 'opencode', 'gemini', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the specific model identifier."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> str:
        """Generates raw text response given a prompt and optional system instruction."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_instruction: str = "",
        temperature: float = 0.1,
    ) -> T:
        """Generates a structured object validated against a Pydantic model schema."""
        pass
