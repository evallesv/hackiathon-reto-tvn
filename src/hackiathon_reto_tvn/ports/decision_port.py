"""Decision Model Port specification using clean architecture / hexagonal pattern.

Defines the contract for non-generative System One decision and classification models:
- Cloudflare Clef (@cf/cloudflare/clef / @cf/cloudflare/clef-flash)
- TypeSafe Jev (jev-latest / systemone API)
- Mock (Deterministic testing & offline fallback)
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Supported System One decision question types."""

    NOUL = "noul"  # Calibrated boolean yes/no probability
    CHOICE = "choice"  # Selection from predefined categories
    SCORE = "score"  # Numerical score evaluated against a rubric


class NoulQuestion(BaseModel):
    """Boolean question returning probability of 'yes'."""

    type: QuestionType = QuestionType.NOUL
    instructions: str


class ChoiceQuestion(BaseModel):
    """Multiple choice question returning winning option and probabilities."""

    type: QuestionType = QuestionType.CHOICE
    instructions: str
    options: Optional[List[str]] = None
    criteria: Optional[Dict[str, str]] = None


class ScoreQuestion(BaseModel):
    """Rating scale question returning expected score."""

    type: QuestionType = QuestionType.SCORE
    instructions: str
    criteria: Optional[List[str]] = None
    min_score: float = 0.0
    max_score: float = 1.0


QuestionDefinition = Union[NoulQuestion, ChoiceQuestion, ScoreQuestion]


class NoulAnswer(BaseModel):
    """Result for a noul (boolean) question."""

    probability: float = Field(ge=0.0, le=1.0)
    answer: bool = False


class ChoiceAnswer(BaseModel):
    """Result for a choice (classification) question."""

    answer: str
    probabilities: Dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0


class ScoreAnswer(BaseModel):
    """Result for a score question."""

    expected_score: float
    probabilities: Dict[str, float] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    """Aggregated decisions and probabilities for a batch of questions."""

    answers: Dict[str, Union[NoulAnswer, ChoiceAnswer, ScoreAnswer]] = Field(default_factory=dict)
    model_name: str = ""
    provider_name: str = ""
    raw_response: Optional[Dict[str, Any]] = None

    def get_noul(self, key: str, default: float = 0.5) -> float:
        """Returns the probability of a noul question."""
        ans = self.answers.get(key)
        if isinstance(ans, NoulAnswer):
            return ans.probability
        return default

    def get_choice(self, key: str, default: str = "") -> str:
        """Returns the winning answer of a choice question."""
        ans = self.answers.get(key)
        if isinstance(ans, ChoiceAnswer):
            return ans.answer
        return default

    def get_score(self, key: str, default: float = 0.5) -> float:
        """Returns the expected score of a score question."""
        ans = self.answers.get(key)
        if isinstance(ans, ScoreAnswer):
            return ans.expected_score
        return default


class BaseDecisionClient(ABC):
    """Abstract interface for System One decision and classification models."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider name (e.g. 'cloudflare', 'jev', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns model identifier (e.g. '@cf/cloudflare/clef')."""
        pass

    @abstractmethod
    async def decide(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Mapping[str, QuestionDefinition],
    ) -> DecisionResult:
        """Evaluates state against a typed question schema and returns structured decisions."""
        pass
