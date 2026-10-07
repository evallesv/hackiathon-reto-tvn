"""Tests for SQLite Storage Adapter."""

from pathlib import Path

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


def _dataset_record(resource_id: str, record_id: int, **payload: object) -> dict[str, object]:
    return {
        "categoria": "gobierno-finanzas",
        "titulo_dataset": "Planilla de prueba",
        "organizacion": "Entidad X",
        "anio": 2026,
        "mes": 9,
        "resource_id": resource_id,
        "record_id": record_id,
        "payload": {"_id": record_id, **payload},
    }


def test_sqlite_storage_creates_datasets_live_and_has_table(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    assert storage.has_table("datasets_live") is False  # el archivo aún no existe

    storage.init_db()
    assert storage.has_table("datasets_live") is True
    assert storage.get_stats()["total_datasets"] == 0


def test_sqlite_storage_replace_dataset_records_preserves_nulls_and_replaces(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    storage.init_db()

    first = [_dataset_record("res-1", 1, salario=None), _dataset_record("res-1", 2, salario="1,200.00")]
    assert storage.replace_dataset_records("planilla-2026", first) == 2

    # Una segunda corrida con otro recurso reemplaza el dataset completo: no quedan filas viejas.
    second = [_dataset_record("res-2", 1, salario="900.00")]
    assert storage.replace_dataset_records("planilla-2026", second) == 1
    assert storage.get_stats()["total_datasets"] == 1

    with storage.get_connection() as conn:
        row = conn.execute("SELECT categoria, anio, mes, payload_json FROM datasets_live").fetchone()
    assert row["categoria"] == "gobierno-finanzas"
    assert (row["anio"], row["mes"]) == (2026, 9)
    assert '"salario": "900.00"' in row["payload_json"]


def test_sqlite_storage_replace_dataset_records_keeps_null_values(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    storage.init_db()
    storage.replace_dataset_records("planilla-2026", [_dataset_record("res-1", 1, salario=None)])

    with storage.get_connection() as conn:
        payload = conn.execute("SELECT payload_json FROM datasets_live").fetchone()["payload_json"]
    assert '"salario": null' in payload  # nunca se imputa 0


def test_sqlite_storage_prune_datasets(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "test.db")
    storage.init_db()
    storage.replace_dataset_records("a", [_dataset_record("res-a", 1)])
    storage.replace_dataset_records("b", [_dataset_record("res-b", 1)])

    assert storage.prune_datasets(["a"]) == 1
    assert storage.get_stats()["total_datasets"] == 1
    assert storage.prune_datasets([]) == 1
    assert storage.get_stats()["total_datasets"] == 0
