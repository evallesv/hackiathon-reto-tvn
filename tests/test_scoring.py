"""Unit tests for the Attention Score Engine (Puntaje de Atención)."""

from hackiathon_reto_tvn.domain.models import (
    ComponentesPuntaje,
    EstadoEvidencia,
    FichaCaso,
    RangoPuntaje,
)
from hackiathon_reto_tvn.domain.scoring import ScoringEngine


def test_scoring_formula_exact() -> None:
    # Componentes al 100% (1.0 cada uno)
    c_max = ComponentesPuntaje(
        relevancia=1.0,
        impacto_potencial=1.0,
        urgencia=1.0,
        novedad=1.0,
        evidencia_disponible=1.0,
    )
    score_max = ScoringEngine.calculate_score(c_max)
    assert score_max.valor_total == 100.0
    assert score_max.rango == RangoPuntaje.ALTO

    # Componentes en cero
    c_zero = ComponentesPuntaje(
        relevancia=0.0,
        impacto_potencial=0.0,
        urgencia=0.0,
        novedad=0.0,
        evidencia_disponible=0.0,
    )
    score_zero = ScoringEngine.calculate_score(c_zero)
    assert score_zero.valor_total == 0.0
    assert score_zero.rango == RangoPuntaje.BAJO


def test_scoring_ranges_non_overlapping() -> None:
    # Bajo: [0, 40)
    c_bajo = ComponentesPuntaje(
        relevancia=0.5,  # 15
        impacto_potencial=0.4,  # 10
        urgencia=0.4,  # 8
        novedad=0.2,  # 3
        evidencia_disponible=0.2,  # 2  Total = 38.0
    )
    res_bajo = ScoringEngine.calculate_score(c_bajo)
    assert res_bajo.valor_total == 38.0
    assert res_bajo.rango == RangoPuntaje.BAJO

    # Medio: [40, 70)
    c_medio = ComponentesPuntaje(
        relevancia=0.6,  # 18
        impacto_potencial=0.6,  # 15
        urgencia=0.5,  # 10
        novedad=0.4,  # 6
        evidencia_disponible=0.5,  # 5  Total = 54.0
    )
    res_medio = ScoringEngine.calculate_score(c_medio)
    assert res_medio.valor_total == 54.0
    assert res_medio.rango == RangoPuntaje.MEDIO

    # Alto: [70, 100]
    c_alto = ComponentesPuntaje(
        relevancia=0.9,  # 27
        impacto_potencial=0.8,  # 20
        urgencia=0.8,  # 16
        novedad=0.6,  # 9
        evidencia_disponible=0.7,  # 7  Total = 79.0
    )
    res_alto = ScoringEngine.calculate_score(c_alto)
    assert res_alto.valor_total == 79.0
    assert res_alto.rango == RangoPuntaje.ALTO


def test_tie_breaking_order() -> None:
    # Dos casos con exactamente el mismo puntaje total (70.0)
    # Caso A: urgencia 0.8
    # Caso B: urgencia 0.6
    comp_a = ComponentesPuntaje(
        relevancia=0.8, impacto_potencial=0.6, urgencia=0.8, novedad=0.6, evidencia_disponible=0.6
    )
    comp_b = ComponentesPuntaje(
        relevancia=0.9, impacto_potencial=0.6, urgencia=0.6, novedad=0.6, evidencia_disponible=0.6
    )

    caso_a = FichaCaso(
        id_caso="CASO-001",
        puntaje=70.0,
        componentes=comp_a,
        estado_evidencia=EstadoEvidencia.PARCIAL,
    )
    caso_b = FichaCaso(
        id_caso="CASO-002",
        puntaje=70.0,
        componentes=comp_b,
        estado_evidencia=EstadoEvidencia.PARCIAL,
    )

    # El desempate debe priorizar mayor urgencia (caso_a tiene 0.8 frente a 0.6)
    ranked = ScoringEngine.rank_cases([caso_b, caso_a])
    assert ranked[0].id_caso == "CASO-001"
    assert ranked[1].id_caso == "CASO-002"


def test_high_priority_insufficient_evidence_guardrail() -> None:
    comp = ComponentesPuntaje(
        relevancia=1.0, impacto_potencial=1.0, urgencia=1.0, novedad=1.0, evidencia_disponible=0.0
    )
    caso = FichaCaso(
        id_caso="CASO-ALERT",
        puntaje=90.0,
        componentes=comp,
        estado_evidencia=EstadoEvidencia.INSUFICIENTE,
    )

    can_publish, msg = ScoringEngine.can_publish_draft(caso)
    assert not can_publish
    assert "requiere investigación" in msg
    assert "no habilita publicación" in msg
