"""Tests for SQLite Storage Adapter."""

from pathlib import Path

import pytest

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage


def test_sqlite_storage_init_and_stats(tmp_path: Path) -> None:
    db_file = tmp_path / "test_copilot.db"
    storage = SQLiteStorage(db_file)
    storage.init_db()

    stats = storage.get_stats()
    assert stats["db_path"] == str(db_file)
    assert stats["total_noticias"] == 0
    assert stats["total_indicadores"] == 0
    assert stats["total_eventos"] == 0
    assert stats["total_runs"] == 0
    assert stats["latest_run"] is None


def test_sqlite_storage_upsert_noticias(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    storage.init_db()

    items = [
        {
            "id_noticia": "NOT-001",
            "titulo": "Noticia de prueba 1",
            "url": "https://example.com/noticia-1",
            "medio": "TVN Noticias",
            "tema": "economia",
            "fecha_publicacion": "2026-10-06T12:00:00Z",
        },
        {
            "id_noticia": "NOT-002",
            "titulo": "Noticia de prueba 2",
            "url": "https://example.com/noticia-2",
            "medio": "TVN Noticias",
            "tema": "nacionales",
            "fecha_publicacion": "2026-10-06T13:00:00Z",
        },
    ]

    count = storage.upsert_noticias(items)
    assert count == 2

    # Duplicate URL upsert should not increase count
    items_updated = [
        {
            "id_noticia": "NOT-001",
            "titulo": "Noticia de prueba 1 actualizada",
            "url": "https://example.com/noticia-1",
            "medio": "TVN Noticias",
        }
    ]
    count_update = storage.upsert_noticias(items_updated)
    assert count_update == 1

    latest = storage.get_latest_noticias(limit=10)
    assert len(latest) == 2
    # Verify title was updated on conflict
    noticia_1 = next(n for n in latest if n["url"] == "https://example.com/noticia-1")
    assert noticia_1["titulo"] == "Noticia de prueba 1 actualizada"


def test_sqlite_storage_upsert_indicadores_and_eventos(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    storage.init_db()

    # Indicadores
    ind_items = [
        {
            "pais_iso3": "PAN",
            "indicador_id": "NY.GDP.MKTP.KD.ZG",
            "anio": 2023,
            "valor": 7.3,
            "unidad": "%",
            "fuente_url": "https://api.worldbank.org",
        },
        {
            "pais_iso3": "PAN",
            "indicador_id": "FP.CPI.TOTL.ZG",
            "anio": 2023,
            "valor": 1.5,
            "unidad": "%",
            "fuente_url": "https://api.worldbank.org",
        },
    ]
    c_ind = storage.upsert_indicadores(ind_items)
    assert c_ind == 2

    # Eventos
    ev_items = [
        {
            "id": "us1000abc",
            "magnitude": 4.5,
            "place": "Golfo de Chiriquí",
            "time": 1710386100000,
            "latitud": 7.42,
            "longitud": -82.85,
        }
    ]
    c_ev = storage.upsert_eventos(ev_items)
    assert c_ev == 1

    # Record run
    storage.record_run(
        fuente="tvn_rss",
        estado="SUCCESS",
        registros_nuevos=2,
        detalles="Ingested 2 items",
        started_at="2026-10-06T12:00:00Z",
        finished_at="2026-10-06T12:00:01Z",
    )

    stats = storage.get_stats()
    assert stats["total_indicadores"] == 2
    assert stats["total_eventos"] == 1
    assert stats["total_runs"] == 1
    assert stats["latest_run"]["fuente"] == "tvn_rss"

    runs = storage.get_latest_runs(limit=5)
    assert len(runs) == 1
    assert runs[0]["estado"] == "SUCCESS"


def test_usgs_storage_preserves_real_zero_updated_timestamp(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "zero.db")
    storage.init_db()
    storage.upsert_eventos([{"id": "zero-update", "magnitude": 3.0, "place": "Panama", "time": 1, "updated": 0}])

    assert storage.get_latest_eventos()[0]["updated"] == 0


@pytest.mark.parametrize("field", ["magnitude", "time", "place"])
@pytest.mark.parametrize("explicit_null", [False, True])
def test_usgs_storage_excludes_missing_required_data_and_continues_valid_records(
    tmp_path: Path, field: str, explicit_null: bool
) -> None:
    storage = SQLiteStorage(tmp_path / "partial.db")
    storage.init_db()
    incomplete = {"id": "incomplete", "magnitude": 3.0, "place": "Panamá", "time": 1}
    if explicit_null:
        incomplete[field] = None
    else:
        incomplete.pop(field)
    valid = {"id": "zero", "magnitude": 0.0, "place": "Panamá", "time": 0}

    assert storage.upsert_eventos([incomplete, valid]) == 1
    [stored] = storage.get_latest_eventos()
    assert stored["id"] == "zero"
    assert stored["magnitude"] == 0.0
    assert stored["time"] == 0
    assert stored["status"] is None


def test_usgs_storage_synchronizes_corrected_coordinates_and_time(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "corrected.db")
    storage.init_db()
    storage.upsert_eventos([{"id": "same", "magnitude": 3.0, "place": "Panamá", "time": 1}])
    corrected = {
        "id": "same",
        "magnitude": 3.1,
        "place": "Panamá",
        "time": 2,
        "latitud": 0.0,
        "longitud": 0.0,
        "profundidad": 0.0,
        "url": "https://example.com/corrected",
    }
    storage.upsert_eventos([corrected])
    [stored] = storage.get_latest_eventos()
    assert (stored["time"], stored["latitud"], stored["longitud"], stored["profundidad"]) == (2, 0.0, 0.0, 0.0)
    assert stored["url"] == corrected["url"]
