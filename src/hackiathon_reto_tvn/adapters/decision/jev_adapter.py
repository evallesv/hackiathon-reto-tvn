"""TypeSafe Jev Decision Adapter.

Implements System One decision model using the commercial TypeSafe Jev API.
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


class JevAdapter(BaseDecisionClient):
    """Adapter for TypeSafe AI Jev decision model."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://opencode.ai/zen/v1/systemone",
        model: str = "jev-1.13-free",
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            result = self._parse_response(data)
            self._validate_requested_answers(result, questions)
            return result
        except Exception as exc:
            logger.warning(
                f"Error calling Jev System One API ({self.model}): {exc}. "
                "Falling back to MockDecisionAdapter for resilient offline operation (T10)."
            )
            from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter

            fallback = MockDecisionAdapter(model_name=f"{self.model}-offline-fallback")
            return await fallback.decide(state=state, questions=questions)

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
                if q_def.criteria:
                    entry["criteria"] = q_def.criteria
                elif q_def.options:
                    # Jev requires criteria as a mapping of option keys to criteria descriptions
                    entry["criteria"] = {opt: f"Opción o categoría {opt}" for opt in q_def.options}
                serialized[q_id] = entry
            elif isinstance(q_def, ScoreQuestion):
                entry = {
                    "type": "score",
                    "instructions": q_def.instructions,
                }
                if q_def.criteria and isinstance(q_def.criteria, list):
                    entry["criteria"] = q_def.criteria
                elif q_def.criteria and isinstance(q_def.criteria, dict):
                    entry["criteria"] = list(q_def.criteria.values())
                else:
                    # Jev requires criteria to be an ordered rubric list of 2 to 10 descriptions
                    entry["criteria"] = [
                        "Nivel bajo (mínima relevancia o impacto)",
                        "Nivel medio (relevancia o impacto moderado)",
                        "Nivel alto (alta prioridad, urgencia o impacto nacional)",
                    ]
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
        """Parses Jev answers dictionary."""
        raw_answers = data.get("answers", data)
        parsed_answers: Dict[str, Union[NoulAnswer, ChoiceAnswer, ScoreAnswer]] = {}

        for key, ans_data in raw_answers.items():
            if not isinstance(ans_data, dict):
                continue

            if "expected_score" in ans_data or "score" in ans_data:
                score_val = ans_data.get("score") if "score" in ans_data else ans_data.get("expected_score")
                if score_val is None:
                    raise ValueError(f"Puntaje nulo para '{key}'.")
                raw_score = float(score_val)
                if not math.isfinite(raw_score):
                    raise ValueError(f"Puntaje no finito para '{key}'.")
                legend = ans_data.get("legend", {})
                if isinstance(legend, dict) and len(legend) > 1:
                    max_idx = float(len(legend) - 1)
                    normalized_score = min(1.0, max(0.0, raw_score / max_idx))
                else:
                    normalized_score = min(1.0, max(0.0, raw_score))

                parsed_answers[key] = ScoreAnswer(
                    expected_score=normalized_score,
                    probabilities={k: float(v) for k, v in ans_data.get("probabilities", {}).items()},
                )
            elif (
                "choice" in ans_data
                or "confidence" in ans_data
                or ("probabilities" in ans_data and "probability" not in ans_data and "noul" not in ans_data)
            ):
                raw_choice = ans_data.get("choice") if "choice" in ans_data else ans_data.get("answer")
                if not isinstance(raw_choice, str):
                    raise ValueError(f"Respuesta de clasificación inválida para '{key}'.")
                parsed_answers[key] = ChoiceAnswer(
                    answer=raw_choice,
                    probabilities={k: float(v) for k, v in ans_data.get("probabilities", {}).items()},
                    confidence=float(ans_data.get("confidence", 0.0)),
                )
            elif "noul" in ans_data or "probability" in ans_data:
                noul_val = ans_data.get("noul") if "noul" in ans_data else ans_data.get("probability")
                if noul_val is None:
                    raise ValueError(f"Probabilidad nula para '{key}'.")
                prob = float(noul_val)
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
