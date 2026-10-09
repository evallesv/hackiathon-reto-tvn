"""Prepare development evidence for human adjudication without inventing review outcomes."""

import json
from typing import Any


def prepare_review_rows(report: dict[str, Any], source_records: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Export answer units; a reviewer must identify and judge each factual claim separately."""
    if not str(report.get("resumen_benchmark", {}).get("modo_evaluacion", "")).startswith("desarrollo"):
        raise ValueError("La planilla local solo admite reportes de desarrollo; no importa etiquetas reservadas.")
    rows = []
    for detail in report.get("detalle", []):
        if detail.get("categoria") != "respuesta_sustentada" or detail.get("es_abstencion"):
            continue
        citations = detail.get("citas", [])
        sources = {
            citation["id_fuente"]: source_records.get(citation["id_fuente"])
            for citation in citations
            if isinstance(citation, dict) and isinstance(citation.get("id_fuente"), str)
        }
        rows.append(
            {
                "id_respuesta": str(detail["id"]),
                "consulta": str(detail.get("consulta", "")),
                "respuesta_completa": str(detail.get("respuesta", "")),
                "citas_emitidas_json": json.dumps(citations, ensure_ascii=False),
                "registros_originales_json": json.dumps(sources, ensure_ascii=False),
                "id_afirmacion_revisada": "",
                "afirmacion_a_evaluar": "",
                "tipo_afirmacion": "",
                "sustento_valido_si_no": "",
                "persona_revisora": "",
                "fecha_revision_utc": "",
                "observaciones": "",
            }
        )
    return rows
