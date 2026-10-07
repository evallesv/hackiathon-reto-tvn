"""TypeSafe Jev Decision Adapter.

Implements System One decision model using the commercial TypeSafe Jev API.
"""

import logging
from collections.abc import Mapping
from typing import Any, Dict, Union

import httpx

from hackiathon_reto_tvn.ports.decision_port import (
    BaseDecisionClient,
    ChoiceAnswer,
    ChoiceQuestion,
    DecisionResult,
    NoulAnswer,
    NoulQuestion,
    QuestionDefinition,
    ScoreAnswer,
    ScoreQuestion,
)

logger = logging.getLogger(__name__)


class JevAdapter(BaseDecisionClient):
    """Adapter for TypeSafe AI Jev decision model."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.typesafe.ai/v1/systemone",
        model: str = "jev-latest",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "jev"

    @property
    def model_name(self) -> str:
        return self.model

    async def decide(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Mapping[str, QuestionDefinition],
    ) -> DecisionResult:
        """Sends state and questions to TypeSafe Jev API endpoint."""
        if not self.api_key:
            raise ValueError("TypeSafe api_key es obligatoria para JevAdapter.")

        formatted_questions = self._serialize_questions(questions)
        payload = {
            "model": self.model,
            "state": state if isinstance(state, (str, dict)) else str(state),
            "questions": formatted_questions,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data)

    def _serialize_questions(self, questions: Mapping[str, QuestionDefinition]) -> Dict[str, Any]:
        """Serializes questions into Jev System One format."""
        serialized: Dict[str, Any] = {}
        for q_id, q_def in questions.items():
            if isinstance(q_def, NoulQuestion):
                serialized[q_id] = {
                    "type": "noul",
                    "instructions": q_def.instructions,
                }
            elif isinstance(q_def, ChoiceQuestion):
                entry: Dict[str, Any] = {
                    "type": "choice",
                    "instructions": q_def.instructions,
                }
                if q_def.options:
                    entry["options"] = q_def.options
                if q_def.criteria:
                    entry["criteria"] = q_def.criteria
                serialized[q_id] = entry
            elif isinstance(q_def, ScoreQuestion):
                entry = {
                    "type": "score",
                    "instructions": q_def.instructions,
                }
                if q_def.criteria:
                    entry["criteria"] = q_def.criteria
                serialized[q_id] = entry
            else:
                serialized[q_id] = q_def.model_dump()
        return serialized

    def _parse_response(self, data: Dict[str, Any]) -> DecisionResult:
        """Parses Jev answers dictionary."""
        raw_answers = data.get("answers", data)
        parsed_answers: Dict[str, Union[NoulAnswer, ChoiceAnswer, ScoreAnswer]] = {}

        for key, ans_data in raw_answers.items():
            if not isinstance(ans_data, dict):
                continue

            if "expected_score" in ans_data:
                parsed_answers[key] = ScoreAnswer(
                    expected_score=float(ans_data.get("expected_score", 0.0)),
                    probabilities={k: float(v) for k, v in ans_data.get("probabilities", {}).items()},
                )
            elif "confidence" in ans_data or ("probabilities" in ans_data and "probability" not in ans_data):
                parsed_answers[key] = ChoiceAnswer(
                    answer=str(ans_data.get("answer", "")),
                    probabilities={k: float(v) for k, v in ans_data.get("probabilities", {}).items()},
                    confidence=float(ans_data.get("confidence", 0.0)),
                )
            elif "probability" in ans_data:
                prob = float(ans_data.get("probability", 0.0))
                raw_val = ans_data.get("answer")
                bool_val = (raw_val is True or raw_val == "yes") if raw_val is not None else (prob >= 0.5)
                parsed_answers[key] = NoulAnswer(
                    probability=prob,
                    answer=bool_val,
                )

        return DecisionResult(
            answers=parsed_answers,
            model_name=self.model,
            provider_name=self.provider_name,
            raw_response=data,
        )
