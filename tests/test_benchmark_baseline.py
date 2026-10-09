"""Tests for BaselineEvaluator, comparative AI baselines, and benchmark execution."""

import pytest
from fastapi.testclient import TestClient

from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.main import app
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
    assert summary["cobertura_citas_porcentaje"] == 100.0
    assert summary["tasa_abstencion_porcentaje"] >= 80.0
    assert summary["resistencia_adversarial_porcentaje"] == 100.0
    assert summary["latencia_mediana_ms"] >= 0.0


@pytest.mark.asyncio
async def test_run_benchmark_suite_refuses_public_reserved_labels(evaluator: BaselineEvaluator) -> None:
    report = await evaluator.run_benchmark_suite(only_dev=False)

    assert "error" in report
    assert "custodia externa" in report["error"]


def test_api_benchmark_metrics_endpoint() -> None:
    """Prueba de integración HTTP para GET /api/v1/copilot/benchmark/metrics."""
    client = TestClient(app)
    res = client.get("/api/v1/copilot/benchmark/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "resumen_benchmark" in data
    assert "comparativa_baselines" in data
