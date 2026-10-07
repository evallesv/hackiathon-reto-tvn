"""Attention Score Engine (Puntaje de Atención).

Implements the official hackathon scoring formula:
P = 30*R + 25*I + 20*U + 15*N + 10*E

Ranges without overlap:
- bajo:  [0, 40)
- medio: [40, 70)
- alto:  [70, 100]

Tie breaking rule:
1. Higher Urgency (U)
2. Alphanumeric ID

Evidence state is strictly INDEPENDENT of the attention score:
- 'insuficiente'
- 'parcial'
- 'suficiente_para_borrador'
"""

from typing import List, Tuple

from hackiathon_reto_tvn.domain.models import (
    ComponentesPuntaje,
    EstadoEvidencia,
    FichaCaso,
    PuntajeAtencion,
    RangoPuntaje,
)


class ScoringEngine:
    """Calculates and validates attention scores and ranking orders."""

    PESO_R = 30.0
    PESO_I = 25.0
    PESO_U = 20.0
    PESO_N = 15.0
    PESO_E = 10.0
    VERSION_REGLAS = "v1.0"

    @classmethod
    def calculate_score(
        cls,
        componentes: ComponentesPuntaje,
        custom_weights: Tuple[float, float, float, float, float] | None = None,
    ) -> PuntajeAtencion:
        """Calculate attention score P = 30R + 25I + 20U + 15N + 10E.

        All components must be in [0.0, 1.0].
        """
        w_r, w_i, w_u, w_n, w_e = (
            custom_weights if custom_weights else (cls.PESO_R, cls.PESO_I, cls.PESO_U, cls.PESO_N, cls.PESO_E)
        )

        p = (
            w_r * componentes.relevancia
            + w_i * componentes.impacto_potencial
            + w_u * componentes.urgencia
            + w_n * componentes.novedad
            + w_e * componentes.evidencia_disponible
        )

        # Round to 2 decimals, clamp to [0, 100]
        p = max(0.0, min(100.0, round(p, 2)))

        if p < 40.0:
            rango = RangoPuntaje.BAJO
        elif p < 70.0:
            rango = RangoPuntaje.MEDIO
        else:
            rango = RangoPuntaje.ALTO

        formula = f"P = {w_r:.0f}R + {w_i:.0f}I + {w_u:.0f}U + {w_n:.0f}N + {w_e:.0f}E"
        justificacion = (
            f"Calculado con R={componentes.relevancia:.2f}, I={componentes.impacto_potencial:.2f}, "
            f"U={componentes.urgencia:.2f}, N={componentes.novedad:.2f}, E={componentes.evidencia_disponible:.2f}. "
            f"Rango clasificado: {rango.value}."
        )

        return PuntajeAtencion(
            valor_total=p,
            rango=rango,
            componentes=componentes,
            formula_aplicada=formula,
            version_reglas=cls.VERSION_REGLAS,
            justificacion=justificacion,
        )

    @staticmethod
    def evaluate_evidence_state(
        num_fuentes_primarias: int,
        tiene_verificacion_cruzada: bool,
        tiene_datos_oficiales: bool,
    ) -> EstadoEvidencia:
        """Derive evidence state independently from attention score."""
        if num_fuentes_primarias >= 2 and (tiene_verificacion_cruzada or tiene_datos_oficiales):
            return EstadoEvidencia.SUFICIENTE_PARA_BORRADOR
        elif num_fuentes_primarias >= 1:
            return EstadoEvidencia.PARCIAL
        return EstadoEvidencia.INSUFICIENTE

    @classmethod
    def rank_cases(cls, cases: List[FichaCaso]) -> List[FichaCaso]:
        """Rank cases according to:

        1. Total Score descending (-case.puntaje)
        2. Tie break 1: Urgency descending (-case.componentes.urgencia)
        3. Tie break 2: ID ascending (case.id_caso)
        """
        return sorted(
            cases,
            key=lambda c: (-c.puntaje, -c.componentes.urgencia, c.id_caso),
        )

    @staticmethod
    def can_publish_draft(caso: FichaCaso) -> Tuple[bool, str]:
        """Checks if a case qualifies to proceed to publication draft.

        Rule: A high score with insufficient evidence requires investigation;
        does not enable publication.
        """
        if caso.estado_evidencia == EstadoEvidencia.INSUFICIENTE:
            return (
                False,
                "Prioridad alta o media con evidencia insuficiente requiere investigación; "
                "no habilita publicación de borrador.",
            )
        return True, "Habilitado para revisión y elaboración de borrador."
