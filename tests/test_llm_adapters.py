"""Unit tests for interchangeable LLM adapters (OpenCode, Gemini, Mock)."""

import pytest

from hackiathon_reto_tvn.adapters.llm.factory import get_llm_client
from hackiathon_reto_tvn.adapters.llm.gemini_adapter import GeminiAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.adapters.llm.opencode_adapter import OpenCodeAdapter
from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.domain.models import BorradorEditorial
from hackiathon_reto_tvn.domain.safety import SafetyGuard


@pytest.mark.asyncio
async def test_mock_adapter_generate_text() -> None:
    adapter = MockLLMAdapter()
    assert adapter.provider_name == "mock"
    assert "mock" in adapter.model_name

    res = await adapter.generate_text("Pregunta de prueba sobre noticias")
    assert "Análisis editorial generado" in res


@pytest.mark.asyncio
async def test_mock_adapter_generate_structured_borrador() -> None:
    adapter = MockLLMAdapter()
    borrador = await adapter.generate_structured(
        prompt=(
            "Generar brief para caso 1\n"
            + SafetyGuard.format_as_data_payload("NOT-TEST-1", "Titular de prueba verificable", "")
        ),
        response_model=BorradorEditorial,
    )
    assert isinstance(borrador, BorradorEditorial)
    assert borrador.titulo_propuesto != ""
    assert len(borrador.preguntas_investigacion) >= 3
    assert borrador.basado_unicamente_en_titular_metadatos is True


def test_opencode_adapter_initialization() -> None:
    adapter = OpenCodeAdapter(
        api_key="test-key",
        base_url="https://opencode.ai/zen/go/v1",
        model="muse-spark-1.3-contributor",
    )
    assert adapter.provider_name == "opencode"
    assert adapter.model_name == "muse-spark-1.3-contributor"


def test_gemini_adapter_initialization() -> None:
    adapter = GeminiAdapter(
        api_key="test-key",
        model="gemini-2.5-flash",
    )
    assert adapter.provider_name == "gemini"
    assert adapter.model_name == "gemini-2.5-flash"


def test_factory_selection_via_settings() -> None:
    cfg_opencode = Settings(LLM_PROVIDER="opencode", OPENCODE_MODEL="muse-spark-1.3-contributor")
    client_opencode = get_llm_client(cfg_opencode)
    assert isinstance(client_opencode, OpenCodeAdapter)
    assert client_opencode.model_name == "muse-spark-1.3-contributor"

    cfg_gemini = Settings(LLM_PROVIDER="gemini")
    client_gemini = get_llm_client(cfg_gemini)
    assert isinstance(client_gemini, GeminiAdapter)
    assert client_gemini.model_name == "gemini-2.5-flash"

    cfg_mock = Settings(LLM_PROVIDER="mock")
    client_mock = get_llm_client(cfg_mock)
    assert isinstance(client_mock, MockLLMAdapter)


@pytest.mark.asyncio
async def test_opencode_adapter_generate_text_responses_api() -> None:
    from unittest.mock import AsyncMock, MagicMock

    adapter = OpenCodeAdapter(api_key="test-key", model="muse-spark-1.3-contributor")
    mock_resp = MagicMock()
    mock_resp.output_text = "Texto editorial generado por OpenCode"

    adapter._client.responses.create = AsyncMock(return_value=mock_resp)

    res = await adapter.generate_text("Prompt de prueba")
    assert res == "Texto editorial generado por OpenCode"
    adapter._client.responses.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_opencode_adapter_generate_structured_responses_api() -> None:
    from unittest.mock import AsyncMock, MagicMock

    from pydantic import BaseModel

    class DummyModel(BaseModel):
        campo: str

    adapter = OpenCodeAdapter(api_key="test-key", model="muse-spark-1.3-contributor")
    mock_resp = MagicMock()
    mock_resp.output_text = '{"campo": "valor_generado"}'

    adapter._client.responses.create = AsyncMock(return_value=mock_resp)

    obj = await adapter.generate_structured("Prompt estructurado", DummyModel)
    assert obj.campo == "valor_generado"
    adapter._client.responses.create.assert_awaited_once()
