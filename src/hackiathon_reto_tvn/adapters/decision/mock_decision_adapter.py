"""Mock Decision Adapter for deterministic tests, CI runs, and offline demo fallback (T10)."""

import logging
from collections.abc import Mapping
from typing import Any, Dict, Union

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


class MockDecisionAdapter(BaseDecisionClient):
    """Deterministic offline decision client mimicking Cloudflare Clef / Jev."""

    def __init__(self, model_name: str = "mock-clef-offline") -> None:
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def decide(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Mapping[str, QuestionDefinition],
    ) -> DecisionResult:
        """Evaluates state deterministically based on keyword and context cues."""
        state_text = state if isinstance(state, str) else str(state)
        state_lower = state_text.lower()
        answers: Dict[str, Union[NoulAnswer, ChoiceAnswer, ScoreAnswer]] = {}

        for q_id, q_def in questions.items():
            if isinstance(q_def, NoulQuestion):
                prob = self._evaluate_noul(q_id, state_lower)
                answers[q_id] = NoulAnswer(probability=prob, answer=(prob >= 0.5))

            elif isinstance(q_def, ChoiceQuestion):
                options = q_def.options or (list(q_def.criteria.keys()) if q_def.criteria else [])
                choice_ans, probs, conf = self._evaluate_choice(q_id, state_lower, options)
                answers[q_id] = ChoiceAnswer(answer=choice_ans, probabilities=probs, confidence=conf)

            elif isinstance(q_def, ScoreQuestion):
                score, probs = self._evaluate_score(q_id, state_lower, q_def.min_score, q_def.max_score)
                answers[q_id] = ScoreAnswer(expected_score=score, probabilities=probs)

        return DecisionResult(
            answers=answers,
            model_name=self._model_name,
            provider_name=self.provider_name,
            raw_response={"mock": True},
        )

    def _evaluate_noul(self, q_id: str, state_lower: str) -> float:
        """Returns deterministic probability for boolean questions."""
        if "discrepancia" in q_id or "contradiccion" in q_id:
            # Check for conflicting amounts or contradictory statements
            has_conflicting_numbers = ("15 millones" in state_lower and "28 millones" in state_lower) or (
                "fuente a" in state_lower and "fuente b" in state_lower
            )
            return 0.95 if has_conflicting_numbers else 0.05

        if "urgente" in q_id or "inmediata" in q_id:
            if "alerta" in state_lower or "colapso" in state_lower or "sismo" in state_lower:
                return 0.90
            return 0.40

        if "relevante_panama" in q_id:
            return 0.95 if ("panamá" in state_lower or "panama" in state_lower) else 0.40

        return 0.50

    def _evaluate_choice(self, q_id: str, state_lower: str, options: list[str]) -> tuple[str, Dict[str, float], float]:
        """Returns winning choice option and probability distribution."""
        if not options:
            return ("default", {"default": 1.0}, 1.0)

        if "tipo_afirmacion" in q_id or "claim_type" in q_id:
            if any(k in state_lower for k in ["anuncia", "declaró", "declara", "según"]):
                winner = "declaracion" if "declaracion" in options else options[0]
            elif any(k in state_lower for k in ["podría", "estima", "posiblemente"]):
                winner = "inferencia" if "inferencia" in options else options[0]
            else:
                winner = "hecho" if "hecho" in options else options[0]

            probs = {opt: (0.90 if opt == winner else (0.10 / max(1, len(options) - 1))) for opt in options}
            return (winner, probs, 0.90)

        if "tema" in q_id or "categoria" in q_id:
            if "canal" in state_lower or "puerto" in state_lower:
                winner = "logistica_canal" if "logistica_canal" in options else options[0]
            elif "econom" in state_lower or "banco" in state_lower or "inflacion" in state_lower:
                winner = "economia" if "economia" in options else options[0]
            elif "sismo" in state_lower or "lluvia" in state_lower or "inundacion" in state_lower:
                winner = "eventos_naturales" if "eventos_naturales" in options else options[0]
            else:
                winner = options[0]

            probs = {opt: (0.85 if opt == winner else (0.15 / max(1, len(options) - 1))) for opt in options}
            return (winner, probs, 0.85)

        winner = options[0]
        probs = {opt: (1.0 / len(options)) for opt in options}
        return (winner, probs, 1.0 / len(options))

    def _evaluate_score(
        self, q_id: str, state_lower: str, min_s: float, max_s: float
    ) -> tuple[float, Dict[str, float]]:
        """Returns expected score for continuous or rubric scales."""
        if "relevancia" in q_id:
            score = 0.95 if ("panamá" in state_lower or "panama" in state_lower) else 0.40
        elif "impacto" in q_id:
            if any(k in state_lower for k in ["canal", "banco", "crisis", "agua", "salud", "economia"]):
                score = 0.85
            else:
                score = 0.50
        elif "urgencia" in q_id:
            if any(k in state_lower for k in ["sismo", "alerta", "urgente", "colapso"]):
                score = 0.80
            else:
                score = 0.65
        elif "novedad" in q_id:
            score = 0.80
        elif "evidencia" in q_id:
            score = 0.70
        else:
            score = (min_s + max_s) / 2.0

        clamped = max(min_s, min(max_s, score))
        probs = {"low": 1.0 - clamped, "high": clamped}
        return (clamped, probs)
