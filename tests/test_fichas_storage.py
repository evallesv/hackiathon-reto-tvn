"""Tests for FichaCaso SQLite storage and human-in-the-loop review persistence."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.domain.models import EstadoRevision
from hackiathon_reto_tvn.main import app


@pytest.fixture
def temp_storage(tmp_path: Path) -> SQLiteStorage:
    db_file = tmp_path / "test_copilot.db"
    storage = SQLiteStorage(db_file)
    storage.init_db()
    return storage


def test_sqlite_fichas_crud(temp_storage: SQLiteStorage) -> None:
    sample_ficha = {
        "id_caso": "CASO-TEST-001",
        "modalidad": "tvn_editorial",
        "ids_fuente": ["NOT-001"],
        "afirmaciones": [{"id_afirmacion": "AF-1", "texto": "Prueba de caso.", "tipo": "hecho", "citas": []}],
        "citas": [],
        "puntaje": 85.5,
        "componentes": {
            "relevancia": 0.9,
            "impacto_potencial": 0.8,
            "urgencia": 0.8,
            "novedad": 0.8,
            "evidencia_disponible": 0.9,
        },
        "estado_evidencia": "suficiente_para_borrador",
        "borrador": {"titulo_propuesto": "Titular de Prueba"},
        "estado_revision": "en_revision",
        "persona_revisora": None,
        "fecha_creacion": "2024-03-10T12:00:00Z",
        "observaciones_revision": None,
    }

    # Upsert
    temp_storage.upsert_ficha(sample_ficha)

    # Get
    retrieved = temp_storage.get_ficha("CASO-TEST-001")
    assert retrieved is not None
    assert retrieved["id_caso"] == "CASO-TEST-001"
    assert retrieved["puntaje"] == 85.5

    # Update review status
    updated = temp_storage.update_review_status(
        id_caso="CASO-TEST-001",
        nuevo_estado="aprobado_como_borrador",
        persona_revisora="Editor Prueba",
        observaciones="Aprobado sin observaciones.",
    )
    assert updated is not None
    assert updated["estado_revision"] == "aprobado_como_borrador"
    assert updated["persona_revisora"] == "Editor Prueba"
    assert updated["observaciones_revision"] == "Aprobado sin observaciones."

    # Check persistence in DB
    refetched = temp_storage.get_ficha("CASO-TEST-001")
    assert refetched is not None
    assert refetched["estado_revision"] == "aprobado_como_borrador"

    # Stats
    stats = temp_storage.get_stats()
    assert stats["total_fichas"] == 1


def test_seed_fichas_from_canonical_jsonl(temp_storage: SQLiteStorage) -> None:
    seed_file = Path("data/fichas.jsonl")
    assert seed_file.exists(), "data/fichas.jsonl must exist"

    count = temp_storage.seed_fichas_from_jsonl(seed_file)
    assert count == 5

    all_fichas = temp_storage.get_all_fichas()
    assert len(all_fichas) == 5
    # Verify ordering by score descending
    scores = [f["puntaje"] for f in all_fichas]
    assert scores == sorted(scores, reverse=True)


def test_fichas_api_endpoints() -> None:
    client = TestClient(app)

    # 1. Get all fichas
    resp = client.get("/api/v1/copilot/fichas")
    assert resp.status_code == 200
    fichas = resp.json()
    assert len(fichas) >= 5

    # 2. Get specific ficha
    resp_one = client.get("/api/v1/copilot/fichas/CASO-001")
    assert resp_one.status_code == 200
    data = resp_one.json()
    assert data["id_caso"] == "CASO-001"

    # 3. Export fichas
    resp_exp = client.get("/api/v1/copilot/fichas/export")
    assert resp_exp.status_code == 200
    export_list = resp_exp.json()
    assert isinstance(export_list, list)
    assert len(export_list) >= 5

    # 4. Update review status
    rev_payload = {
        "caso_id": "CASO-002",
        "nuevo_estado": EstadoRevision.APROBADO_COMO_BORRADOR.value,
        "persona_revisora": "Editor Jurado",
        "observaciones": "Aprobación verificada para emisión en vivo.",
    }
    resp_rev = client.post("/api/v1/copilot/review", json=rev_payload)
    assert resp_rev.status_code == 200
    rev_result = resp_rev.json()
    assert rev_result["estado_revision"] == "aprobado_como_borrador"
    assert rev_result["persona_revisora"] == "Editor Jurado"
