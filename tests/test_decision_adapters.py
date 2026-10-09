"""Unit tests for System One decision models (Cloudflare Clef, Jev, Mock)."""

from unittest.mock import MagicMock, patch

import pytest

from hackiathon_reto_tvn.adapters.decision.cloudflare_clef_adapter import CloudflareClefAdapter
from hackiathon_reto_tvn.adapters.decision.factory import get_decision_client
from hackiathon_reto_tvn.adapters.decision.jev_adapter import JevAdapter
from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.ports.decision_port import (
    ChoiceAnswer,
    ChoiceQuestion,
    DecisionResult,
    NoulAnswer,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
)
from hackiathon_reto_tvn.services.copilot_service import CopilotService


@pytest.mark.asyncio
async def test_mock_decision_adapter_evaluations() -> None:
    """MockDecisionAdapter evaluates noul, choice, and score questions deterministically."""
    adapter = MockDecisionAdapter()
    assert adapter.provider_name == "mock"
    assert adapter.model_name == "mock-clef-offline"

    questions = {
        "relevancia": ScoreQuestion(instructions="Relevancia para Panamá", min_score=0.0, max_score=1.0),
        "impacto": ScoreQuestion(instructions="Impacto socioeconómico", min_score=0.0, max_score=1.0),
        "urgencia": ScoreQuestion(instructions="Urgencia", min_score=0.0, max_score=1.0),
        "novedad": ScoreQuestion(instructions="Novedad", min_score=0.0, max_score=1.0),
        "tipo_afirmacion": ChoiceQuestion(
            instructions="Clasifica titular",
            options=["hecho", "declaracion", "inferencia"],
        ),
        "discrepancia": NoulQuestion(instructions="¿Hay contradicción?"),
    }

    state = "Titular: Presidente anuncia plan de agua en Panamá\nContenido: Proyecto por 15 millones."
    result = await adapter.decide(state=state, questions=questions)

    assert result.get_score("relevancia") == 0.95
    assert result.get_score("impacto") == 0.85
    assert result.get_choice("tipo_afirmacion") == "declaracion"
    assert result.get_noul("discrepancia") == 0.05


@pytest.mark.asyncio
async def test_mock_decision_adapter_contradiction_detection() -> None:
    """MockDecisionAdapter detects conflicting versions in noul questions."""
    adapter = MockDecisionAdapter()
    state = "Versión A: Fuente A afirma 15 millones\nVersión B: Fuente B afirma 28 millones"
    questions = {"discrepancia": NoulQuestion(instructions="¿Existe conflicto?")}

    result = await adapter.decide(state=state, questions=questions)
    assert result.get_noul("discrepancia") == 0.95


def test_cloudflare_clef_adapter_serialization_and_validation() -> None:
    """CloudflareClefAdapter validates required credentials and serializes question schema."""
    with pytest.raises(ValueError, match="account_id y api_token son obligatorios"):
        adapter_invalid = CloudflareClefAdapter(account_id="", api_token="")
        # Calling decide with empty credentials triggers validation
        import asyncio

        asyncio.run(adapter_invalid.decide("test", {}))

    adapter = CloudflareClefAdapter(
        account_id="cf_acc_123",
        api_token="cf_tok_456",
        model="@cf/cloudflare/clef",
    )
    assert adapter.provider_name == "cloudflare"
    assert adapter.model_name == "@cf/cloudflare/clef"

    questions = {
        "is_urgent": NoulQuestion(instructions="¿Es urgente?"),
        "tema": ChoiceQuestion(instructions="Selecciona tema", options=["politica", "economia"]),
        "severidad": ScoreQuestion(instructions="Califica severidad", criteria=["baja", "alta"]),
    }
    serialized = adapter._serialize_questions(questions)
    assert serialized["is_urgent"]["type"] == "noul"
    assert serialized["tema"]["type"] == "choice"
    assert serialized["tema"]["options"] == ["politica", "economia"]
    assert serialized["severidad"]["type"] == "score"


@pytest.mark.asyncio
async def test_cloudflare_clef_adapter_response_parsing() -> None:
    """CloudflareClefAdapter parses result.answers envelope correctly."""
    adapter = CloudflareClefAdapter(
        account_id="cf_acc_123",
        api_token="cf_tok_456",
    )

    mock_response_data = {
        "result": {
            "answers": {
                "is_urgent": {"probability": 0.88, "answer": "yes"},
                "tema": {
                    "answer": "economia",
                    "probabilities": {"economia": 0.9, "politica": 0.1},
                    "confidence": 0.9,
                },
                "score_panama": {
                    "expected_score": 0.92,
                    "probabilities": {"level_1": 0.08, "level_2": 0.92},
                },
            }
        },
        "success": True,
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await adapter.decide(
            state="Noticia de prueba",
            questions={"is_urgent": NoulQuestion(instructions="urgente")},
        )

        assert res.get_noul("is_urgent") == 0.88
        assert res.get_choice("tema") == "economia"
        assert res.get_score("score_panama") == 0.92


@pytest.mark.asyncio
async def test_jev_adapter_parsing_and_serialization() -> None:
    """JevAdapter serializes questions and parses TypeSafe answers."""
    adapter = JevAdapter(api_key="jev_key_xyz", model="jev-latest")
    assert adapter.provider_name == "jev"
    assert adapter.model_name == "jev-latest"

    mock_jev_data = {
        "answers": {
            "discrepancia": {"probability": 0.95, "answer": True},
            "categoria": {
                "answer": "economia",
                "probabilities": {"economia": 0.95},
                "confidence": 0.95,
            },
            "calificacion": {"expected_score": 0.85},
        }
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jev_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await adapter.decide(
            state="Comparativa",
            questions={"discrepancia": NoulQuestion(instructions="Conflicto")},
        )
        assert res.get_noul("discrepancia") == 0.95
        assert res.get_choice("categoria") == "economia"
        assert res.get_score("calificacion") == 0.85


@pytest.mark.asyncio
async def test_jev_adapter_opencode_zen_format() -> None:
    """JevAdapter parses OpenCode Zen formatted response (noul, choice, score with legend)."""
    adapter = JevAdapter(api_key="oc_test_key", model="jev-1.13-free")
    mock_zen_data = {
        "model": "jev-1.13-free",
        "answers": {
            "relevancia": {"type": "noul", "noul": 0.92},
            "categoria": {
                "type": "choice",
                "choice": "economia",
                "confidence": 1.0,
                "probabilities": {"economia": 1.0, "politica": 0.0},
            },
            "severidad": {
                "type": "score",
                "score": 2.0,
                "legend": {"0": "baja", "1": "media", "2": "alta"},
            },
        },
    }
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_zen_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = await adapter.decide(
            state="Noticia de prueba",
            questions={
                "relevancia": NoulQuestion(instructions="Relevante"),
                "categoria": ChoiceQuestion(instructions="Categoría"),
                "severidad": ScoreQuestion(instructions="Severidad"),
            },
        )
        assert res.get_noul("relevancia") == 0.92
        assert res.get_choice("categoria") == "economia"
        # 2.0 / (3 - 1) = 1.0 normalized
        assert res.get_score("severidad") == 1.0


def test_factory_transparent_fallback_and_selection() -> None:
    """Factory returns Cloudflare/Jev when configured, and falls back to Mock when credentials are empty."""
    # 1. Cloudflare with credentials
    s1 = Settings(
        DECISION_PROVIDER="cloudflare",
        CLOUDFLARE_ACCOUNT_ID="acc123",
        CLOUDFLARE_API_TOKEN="tok123",
    )
    client1 = get_decision_client(s1)
    assert isinstance(client1, CloudflareClefAdapter)

    # 2. Cloudflare missing credentials -> Transparent fallback to Mock
    s2 = Settings(
        DECISION_PROVIDER="cloudflare",
        CLOUDFLARE_ACCOUNT_ID="",
        CLOUDFLARE_API_TOKEN="",
    )
    client2 = get_decision_client(s2)
    assert isinstance(client2, MockDecisionAdapter)

    # 3. Jev with Typesafe credentials
    s3 = Settings(
        DECISION_PROVIDER="jev",
        TYPESAFE_API_KEY="key123",
    )
    client3 = get_decision_client(s3)
    assert isinstance(client3, JevAdapter)

    # 3b. Jev with OpenCode credentials (unified key)
    s3b = Settings(
        DECISION_PROVIDER="jev",
        TYPESAFE_API_KEY="",
        OPENCODE_API_KEY="oc_unified_key",
    )
    client3b = get_decision_client(s3b)
    assert isinstance(client3b, JevAdapter)
    assert client3b.api_key == "oc_unified_key"

    # 4. Jev missing credentials -> Transparent fallback to Mock
    s4 = Settings(
        DECISION_PROVIDER="jev",
        TYPESAFE_API_KEY="",
        OPENCODE_API_KEY="",
    )
    client4 = get_decision_client(s4)
    assert isinstance(client4, MockDecisionAdapter)

    # 5. Mock explicit
    s5 = Settings(DECISION_PROVIDER="mock")
    client5 = get_decision_client(s5)
    assert isinstance(client5, MockDecisionAdapter)


@pytest.mark.parametrize("provider", ["cloudflare", "jev"])
@pytest.mark.parametrize(
    "invalid_response",
    [
        "empty",
        "missing_question",
        "empty_answer",
        "wrong_type",
        "null_probability",
        "null_score",
        "empty_choice",
        "null_choice",
    ],
)
@pytest.mark.asyncio
async def test_incomplete_provider_responses_fall_back_with_effective_attribution(
    provider: str, invalid_response: str
) -> None:
    adapter = (
        CloudflareClefAdapter("test-account", "test-token") if provider == "cloudflare" else JevAdapter("test-key")
    )
    questions = {
        "discrepancia": NoulQuestion(instructions="¿Hay discrepancia?"),
        "urgencia": ScoreQuestion(instructions="Urgencia"),
        "tipo_afirmacion": ChoiceQuestion(instructions="Clasifica", options=["hecho", "declaracion"]),
    }
    answers = {
        "discrepancia": {"probability": 0.1},
        "urgencia": {"expected_score": 0.2},
        "tipo_afirmacion": {"answer": "hecho", "confidence": 0.9},
    }
    if invalid_response == "empty":
        answers = {}
    elif invalid_response == "missing_question":
        answers.pop("urgencia")
    elif invalid_response == "empty_answer":
        answers["discrepancia"] = {}
    elif invalid_response == "wrong_type":
        answers["discrepancia"] = {"expected_score": 0.0}
    elif invalid_response == "null_probability":
        answers["discrepancia"] = {"probability": None} if provider == "cloudflare" else {"noul": None}
    elif invalid_response == "null_score":
        answers["urgencia"] = {"expected_score": None} if provider == "cloudflare" else {"score": None}
    elif invalid_response == "empty_choice":
        answers["tipo_afirmacion"] = {"answer": "", "confidence": 0.9}
    else:
        answers["tipo_afirmacion"] = {"answer": None, "confidence": 0.9}
    payload = {"success": True, "result": {"answers": answers}} if provider == "cloudflare" else {"answers": answers}

    with patch("httpx.AsyncClient.post") as mock_post:
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        mock_post.return_value = response
        result = await adapter.decide("Versión A: 15 millones\nVersión B: 28 millones", questions)

    assert result.provider_name == "mock"
    assert result.model_name.endswith("-offline-fallback")
    assert result.get_noul("discrepancia") == 0.95
    assert isinstance(result.answers["urgencia"], ScoreAnswer)
    assert isinstance(result.answers["tipo_afirmacion"], ChoiceAnswer)


@pytest.mark.parametrize("provider", ["cloudflare", "jev"])
@pytest.mark.asyncio
async def test_provider_responses_preserve_legitimate_zero_probabilities_and_scores(provider: str) -> None:
    adapter = (
        CloudflareClefAdapter("test-account", "test-token") if provider == "cloudflare" else JevAdapter("test-key")
    )
    answers = (
        {"discrepancia": {"probability": 0.0}, "urgencia": {"expected_score": 0.0}}
        if provider == "cloudflare"
        else {"discrepancia": {"noul": 0.0}, "urgencia": {"score": 0.0}}
    )
    payload = {"success": True, "result": {"answers": answers}} if provider == "cloudflare" else {"answers": answers}

    with patch("httpx.AsyncClient.post") as mock_post:
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        mock_post.return_value = response
        result = await adapter.decide(
            "Versiones compatibles",
            {
                "discrepancia": NoulQuestion(instructions="Discrepancia"),
                "urgencia": ScoreQuestion(instructions="Urgencia"),
            },
        )

    assert result.provider_name == provider
    assert result.get_noul("discrepancia") == 0.0
    assert result.get_score("urgencia") == 0.0


@pytest.mark.parametrize("answer", [None, ChoiceAnswer(answer=""), ScoreAnswer(expected_score=0.0)])
@pytest.mark.asyncio
async def test_contradiction_service_rejects_missing_or_wrong_answer_types(answer: object) -> None:
    class InvalidDecisionClient(MockDecisionAdapter):
        async def decide(self, state, questions):
            answers = {} if answer is None else {"discrepancia": answer}
            return DecisionResult(answers=answers, provider_name="invalid-client", model_name="incomplete")

    service = CopilotService(
        settings=Settings(_env_file=None, ENVIRONMENT="test", LLM_PROVIDER="mock", DECISION_PROVIDER="mock"),
        llm_client=MockLLMAdapter(),
        decision_client=InvalidDecisionClient(),
    )

    with pytest.raises(ValueError, match="discrepancia.*NoulAnswer"):
        await service.detect_contradictions("La obra cuesta 15 millones", "La obra cuesta 28 millones")


@pytest.mark.asyncio
async def test_contradiction_service_accepts_explicit_zero_probability() -> None:
    class ZeroDecisionClient(MockDecisionAdapter):
        async def decide(self, state, questions):
            return DecisionResult(answers={"discrepancia": NoulAnswer(probability=0.0)}, provider_name="mock")

    service = CopilotService(
        settings=Settings(_env_file=None, ENVIRONMENT="test", LLM_PROVIDER="mock", DECISION_PROVIDER="mock"),
        llm_client=MockLLMAdapter(),
        decision_client=ZeroDecisionClient(),
    )

    result = await service.detect_contradictions("La obra cuesta 15 millones", "La obra cuesta 15 millones")

    assert result["probabilidad_discrepancia"] == 0.0
    assert result["estado"] == "consistente"
