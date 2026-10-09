"""Ensure preparing adjudication material cannot manufacture human evidence or expose jury rows."""

import json

import pytest

from hackiathon_reto_tvn.services.human_review import prepare_review_rows


def test_review_packet_contains_original_records_and_no_automatic_verdict() -> None:
    report = {
        "resumen_benchmark": {"modo_evaluacion": "desarrollo (40); reservado no ejecutado"},
        "detalle": [
            {
                "id": "BM-1",
                "categoria": "respuesta_sustentada",
                "consulta": "¿Qué anunció?",
                "respuesta": "Se anunció una obra.",
                "es_abstencion": False,
                "citas": [{"id_fuente": "N-1", "texto_sustento": "Se anunció una obra."}],
            }
        ],
    }
    [row] = prepare_review_rows(report, {"N-1": {"titulo": "Titular original"}})

    assert json.loads(row["registros_originales_json"]) == {"N-1": {"titulo": "Titular original"}}
    assert row["sustento_valido_si_no"] == ""
    assert row["persona_revisora"] == ""
    assert row["afirmacion_a_evaluar"] == ""


def test_local_review_packet_refuses_external_jury_report() -> None:
    with pytest.raises(ValueError, match="solo admite reportes de desarrollo"):
        prepare_review_rows({"resumen_benchmark": {"modo_evaluacion": "reservado externo (20)"}}, {})
