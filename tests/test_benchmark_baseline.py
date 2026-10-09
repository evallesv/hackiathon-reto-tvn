"""Tests for BaselineEvaluator, comparative AI baselines, and benchmark execution."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.domain.models import QueryResponse
from hackiathon_reto_tvn.main import app
from hackiathon_reto_tvn.ports.decision_port import DecisionResult, QuestionDefinition
from hackiathon_reto_tvn.services.baseline_evaluator import BaselineEvaluator
from hackiathon_reto_tvn.services.copilot_service import CopilotService


@pytest.fixture
def evaluator() -> BaselineEvaluator:
    service = CopilotService(llm_client=MockLLMAdapter())
    return BaselineEvaluator(service=service)


def test_evaluate_ranking_baseline(evaluator: BaselineEvaluator) -> None:
    """Verifica la comparación de ranking por recencia vs Puntaje de Atención P."""
    res = evaluator.evaluate_ranking_baseline(top_n=5)
    assert res["tarea"] == "Ranking y Priorización Editorial"
    assert "baseline_recencia" in res
    assert "copilot_score_p" in res
    assert res["copilot_score_p"]["precision_at_5"] >= res["baseline_recencia"]["precision_at_5"]
    assert "mejora_relativa_porcentaje" in res


def test_benchmark_citation_id_metric_rejects_missing_and_unknown_source_ids() -> None:
    valid_ids = {"NOT-001"}

    assert BaselineEvaluator._citation_ids_are_valid([], valid_ids) is False
    assert BaselineEvaluator._citation_ids_are_valid([{"id_fuente": "FAKE-999"}], valid_ids) is False
    assert BaselineEvaluator._citation_ids_are_valid([{"id_fuente": "NOT-001"}], valid_ids) is True


def test_benchmark_expected_value_matching_uses_boundaries_and_ignores_label_notes() -> None:
    assert BaselineEvaluator._expected_value_present("7.3%", "El indicador fue de 7.3%.") is True
    assert BaselineEvaluator._expected_value_present("7.3%", "El indicador fue de 17.3%.") is False
    assert (
        BaselineEvaluator._expected_value_present(
            "2022-05-10T10:00:00Z (no presentar como evento nuevo)", "Fecha original: 2022-05-10T10:00:00Z."
        )
        is True
    )


def test_offline_evaluation_service_disables_both_live_and_demo_sqlite(evaluator: BaselineEvaluator) -> None:
    service = evaluator._offline_evaluation_service()

    assert service.settings.SQLITE_DB_PATH != evaluator.settings.SQLITE_DB_PATH
    assert service.settings.SQLITE_SNAPSHOT_PATH != evaluator.settings.SQLITE_SNAPSHOT_PATH
    assert not service.settings.SQLITE_DB_PATH.exists()
    assert not service.settings.SQLITE_SNAPSHOT_PATH.exists()


@pytest.mark.asyncio
async def test_evaluate_classification_and_contradictions_baseline(evaluator: BaselineEvaluator) -> None:
    """Compares regex with predictions from the configured decision adapter."""
    res = await evaluator.evaluate_classification_and_contradictions_baseline()
    assert res["tarea"] == "Detección de Contradicciones Fácticas (T05)"
    assert "baseline_regex" in res
    assert "modelo_decision" in res
    assert "f1" in res["baseline_regex"]
    assert "f1" in res["modelo_decision"]
    assert res["modelo_decision"]["provider"] == "mock"
    assert res["modelo_decision"]["f1_tipo"] == "macro"


@pytest.mark.asyncio
async def test_run_benchmark_suite(evaluator: BaselineEvaluator) -> None:
    """Verifica la ejecución del suite de benchmark y el reporte consolidado."""
    report = await evaluator.run_benchmark_suite(only_dev=True)
    summary = report["resumen_benchmark"]

    assert summary["total_consultas_ejecutadas"] == 40
    assert summary["respuestas_sustentadas_con_ids_validos_porcentaje"] == 100.0
    assert summary["consultas_sustentadas_evaluadas"] > 0
    assert summary["respuestas_sustentadas_con_ids_validos"] == summary["consultas_sustentadas_evaluadas"]
    assert "semánticamente" in summary["limitacion_ids_cita"]
    assert summary["respuestas_correctas_con_fuente_esperada"] == 20
    assert summary["respuestas_correctas_con_fuente_esperada_porcentaje"] == 100.0
    assert summary["tasa_abstencion_porcentaje"] >= 80.0
    assert summary["resistencia_adversarial_porcentaje"] == 100.0
    assert summary["latencia_mediana_ms"] >= 0.0


@pytest.mark.asyncio
async def test_benchmark_reports_false_abstentions_and_failures(
    evaluator: BaselineEvaluator, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = evaluator._offline_evaluation_service()
    original_answer = service.answer_query_async

    async def false_abstention(consulta: str, modalidad: str = "tvn_editorial") -> QueryResponse:
        if "crecimiento del PIB de Panamá en 2023" in consulta:
            return QueryResponse(consulta=consulta, respuesta="[ABSTENCIÓN EXPLÍCITA]", es_abstencion=True, citas=[])
        return await original_answer(consulta, modalidad)

    monkeypatch.setattr(service, "answer_query_async", false_abstention)
    monkeypatch.setattr(evaluator, "_offline_evaluation_service", lambda: service)
    report = await evaluator.run_benchmark_suite()

    assert report["resumen_benchmark"]["abstenciones_incorrectas"] == 1
    assert report["resumen_benchmark"]["abstenciones_incorrectas_porcentaje"] == 5.0
    assert "BM-001" in report["fallos"]["abstenciones_incorrectas"]
    assert report["resumen_benchmark"]["consultas_sin_respuesta_evaluadas"] == 7
    assert report["resumen_benchmark"]["abstenciones_correctas"] == 7
    assert report["detalle"][0]["respuesta"] == "[ABSTENCIÓN EXPLÍCITA]"


@pytest.mark.asyncio
async def test_classification_metrics_attribute_mock_fallback_to_actual_provider(evaluator: BaselineEvaluator) -> None:
    class RemoteWithFallback(MockDecisionAdapter):
        @property
        def provider_name(self) -> str:
            return "cloudflare"

        async def decide(
            self, state: str | dict[str, Any], questions: Mapping[str, QuestionDefinition]
        ) -> DecisionResult:
            return await MockDecisionAdapter().decide(state, questions)

    evaluator.service.decision_client = RemoteWithFallback()
    report = await evaluator.evaluate_classification_and_contradictions_baseline()

    assert len(report["detalle"]) == 10
    assert all(row["proveedor_efectivo"] == "mock" and row["uso_fallback"] for row in report["detalle"])
    assert all(isinstance(row["etiqueta_desarrollo"], bool) for row in report["detalle"])
    assert all(row["latencia_ms"] >= 0.0 for row in report["detalle"])

    model = report["modelo_decision"]
    assert model["provider_configurado"] == "cloudflare"
    assert model["provider"] == "mock"
    assert model["ejecuciones_fallback"] == 10
    assert model["ejecuciones_por_proveedor_modelo"] == {"mock/mock-clef-offline": 10}


@pytest.mark.asyncio
async def test_run_benchmark_suite_refuses_public_reserved_labels(evaluator: BaselineEvaluator) -> None:
    report = await evaluator.run_benchmark_suite(only_dev=False)

    assert "error" in report
    assert "archivo externo" in report["error"]


@pytest.mark.asyncio
async def test_run_benchmark_suite_accepts_only_separately_custodied_jury_file(
    evaluator: BaselineEvaluator, tmp_path: Path
) -> None:
    jury_path = tmp_path / "jury.jsonl"
    jury_path.write_text(
        '{"id":"JURY-001","categoria":"respuesta_sustentada",'
        '"consulta":"¿Cuál fue el crecimiento del PIB de Panamá en 2023 según el Banco Mundial?",'
        '"resultado_esperado":"7.3%","id_fuente_esperada":"PAN-NY.GDP.MKTP.KD.ZG-2023",'
        '"conjunto":"reservado_jurado"}\n',
        encoding="utf-8",
    )

    report = await evaluator.run_benchmark_suite(benchmark_path=jury_path, only_dev=False)

    assert report["resumen_benchmark"]["total_consultas_ejecutadas"] == 1
    assert report["resumen_benchmark"]["respuestas_correctas_con_fuente_esperada_porcentaje"] == 100.0
    assert report["resumen_benchmark"]["tasa_abstencion_porcentaje"] is None
    assert report["resumen_benchmark"]["resistencia_adversarial_porcentaje"] is None
    assert report["resumen_benchmark"]["modo_evaluacion"] == "reservado externo (1); independencia no verificada"
    assert report["comparativa_baselines"] == {}
    assert "consulta" not in report["detalle"][0]


@pytest.mark.asyncio
async def test_run_benchmark_suite_rejects_checked_in_benchmark_as_jury(evaluator: BaselineEvaluator) -> None:
    report = await evaluator.run_benchmark_suite(
        benchmark_path=evaluator.settings.DATA_DIR / "benchmark.jsonl",
        only_dev=False,
    )

    assert "error" in report
    assert "fuera del repositorio" in report["error"]


def test_api_benchmark_metrics_endpoint() -> None:
    """Prueba de integración HTTP para GET /api/v1/copilot/benchmark/metrics."""
    client = TestClient(app)
    res = client.get("/api/v1/copilot/benchmark/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "resumen_benchmark" in data
    assert "comparativa_baselines" in data
