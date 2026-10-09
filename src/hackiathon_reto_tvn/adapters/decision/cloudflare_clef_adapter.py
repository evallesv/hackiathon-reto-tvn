"""Cloudflare Clef Decision Adapter (@cf/cloudflare/clef).

Implements System One decision model over Cloudflare Workers AI REST API.
"""

import logging
import math
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


class CloudflareClefAdapter(BaseDecisionClient):
    """Adapter for Cloudflare Workers AI Clef multimodal decision model."""

    def __init__(
        self,
        account_id: str,
        api_token: str,
        model: str = "@cf/cloudflare/clef",
        timeout: float = 30.0,
    ) -> None:
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.timeout = timeout
        self.endpoint_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"

    @property
    def provider_name(self) -> str:
        return "cloudflare"

    @property
    def model_name(self) -> str:
        return self.model

    async def decide(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Mapping[str, QuestionDefinition],
    ) -> DecisionResult:
        """Sends state and question schema to Cloudflare Workers AI and parses probabilistic answers."""
        if not self.account_id or not self.api_token:
            raise ValueError("Cloudflare account_id y api_token son obligatorios para CloudflareClefAdapter.")

        formatted_questions = self._serialize_questions(questions)
        payload = {
            "model": "clef" if "clef" in self.model else self.model,
            "state": state if isinstance(state, (str, dict)) else str(state),
            "questions": formatted_questions,
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            result = self._parse_response(data)
            self._validate_requested_answers(result, questions)
            return result
        except Exception as exc:
            logger.warning(
                f"Error calling Cloudflare Clef API ({self.model}): {exc}. "
                "Falling back to MockDecisionAdapter for resilient offline operation (T10)."
            )
            from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter

            fallback = MockDecisionAdapter(model_name=f"{self.model}-offline-fallback")
            return await fallback.decide(state=state, questions=questions)

    def _serialize_questions(self, questions: Mapping[str, QuestionDefinition]) -> Dict[str, Any]:
        """Serializes questions into Cloudflare Clef / System One schema."""
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

    @staticmethod
    def _validate_requested_answers(result: DecisionResult, questions: Mapping[str, QuestionDefinition]) -> None:
        """Require a usable answer of the requested type before attributing provider success."""
        for key, question in questions.items():
            answer = result.answers.get(key)
            valid_type = (
                isinstance(question, NoulQuestion)
                and isinstance(answer, NoulAnswer)
                or isinstance(question, ChoiceQuestion)
                and isinstance(answer, ChoiceAnswer)
                or isinstance(question, ScoreQuestion)
                and isinstance(answer, ScoreAnswer)
            )
            if not valid_type:
                raise ValueError(f"Respuesta ausente o de tipo incompatible para la pregunta '{key}'.")
            if isinstance(answer, ChoiceAnswer) and not answer.answer.strip():
                raise ValueError(f"Respuesta de clasificación vacía para la pregunta '{key}'.")
            if isinstance(answer, ScoreAnswer) and not math.isfinite(answer.expected_score):
                raise ValueError(f"Puntaje no finito para la pregunta '{key}'.")

    def _parse_response(self, data: Dict[str, Any]) -> DecisionResult:
        """Parses Cloudflare response envelope result.answers."""
        result_body = data.get("result", {})
        raw_answers = result_body.get("answers", result_body)
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
                raw_ans = ans_data.get("answer")
                if not isinstance(raw_ans, str):
                    raise ValueError(f"Respuesta de clasificación inválida para '{key}'.")
                parsed_answers[key] = ChoiceAnswer(
                    answer=raw_ans,
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
            else:
                raw_val = ans_data.get("answer")
                if isinstance(raw_val, bool):
                    parsed_answers[key] = NoulAnswer(probability=1.0 if raw_val else 0.0, answer=raw_val)
                else:
                    parsed_answers[key] = ChoiceAnswer(answer=str(raw_val or ""))

        return DecisionResult(
            answers=parsed_answers,
            model_name=self.model,
            provider_name=self.provider_name,
            raw_response=data,
        )
