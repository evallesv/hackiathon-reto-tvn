"""Tests for immutable, self-contained SQLite data snapshots."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.adapters.data.sqlite_snapshot import SQLiteSnapshotRepository
from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.services.copilot_service import CopilotService


def _create_source_data(directory: Path) -> None:
    raw_dir = directory / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "noticias.csv").write_text(
        "id_noticia,titulo,url,medio,idioma,fecha_publicacion,fecha_deteccion,fecha_extraccion,tema,origen,alcance_texto\n"
        "N-1,Canal de Panamá,https://tvn-2.com/a,TVN,es,2026-10-01,2026-10-01,2026-10-02,logistica,rss,titular_metadatos\n",
        encoding="utf-8",
    )
    (raw_dir / "indicadores.csv").write_text(
        "pais_iso3,indicador_id,anio,valor,unidad,fuente_url,fecha_extraccion,licencia\n"
        "PAN,NY.GDP.MKTP.KD.ZG,2023,,%,https://api.worldbank.org,2026-10-02,CC BY 4.0\n",
        encoding="utf-8",
    )
    (raw_dir / "eventos.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "us7000abcd",
                        "properties": {
                            "mag": 4.2,
                            "time": 1720000000000,
                            "updated": 1720000001000,
                            "place": "Panama region",
                            "status": "reviewed",
                            "url": "https://earthquake.usgs.gov/event/us7000abcd",
                        },
                        "geometry": {"type": "Point", "coordinates": [-80.0, 8.0, 10.0]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    LocalStorageRepository().generate_manifest(directory)


def test_sqlite_snapshot_preserves_records_nulls_and_source_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    snapshot_dir = tmp_path / "snapshot"

    snapshot = SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir)
    snapshot_path = snapshot_dir / "snapshot.sqlite"

    assert snapshot_path.is_file()
    assert (snapshot_dir / "snapshot_manifest.json").is_file()
    assert [item.id_noticia for item in snapshot.load_noticias()] == ["N-1"]
    indicators = snapshot.load_indicadores()
    assert len(indicators) == 540
    assert next(item for item in indicators if item.pais_iso3 == "PAN" and item.anio == 2023).valor is None
    assert [event.id for event in snapshot.load_eventos()] == ["us7000abcd"]
    assert snapshot.metadata()["source_manifest_sha256"]
    assert snapshot.metadata()["counts"] == {
        "eventos": 1,
        "eventos_vivos": 0,
        "indicadores": 540,
        "noticias": 1,
    }
    assert snapshot.metadata()["indicator_grid"] == {
        "expected_combinations": 540,
        "missing_values_are_null_not_imputed": True,
        "null_values": 540,
        "populated_values": 0,
    }
    assert not snapshot.has_table("fichas_casos")


def test_sqlite_snapshot_keeps_indicator_rows_with_missing_identity_fields(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    indicator_path = source / "raw" / "indicadores.csv"
    indicator_path.write_text(
        indicator_path.read_text(encoding="utf-8") + ",,,,,,,\n",
        encoding="utf-8",
    )
    LocalStorageRepository().generate_manifest(source)

    snapshot_dir = tmp_path / "snapshot"
    snapshot = SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir)

    incomplete_rows = [item for item in snapshot.load_indicadores() if item.pais_iso3 is None or item.anio is None]
    assert len(incomplete_rows) == 1
    assert incomplete_rows[0].pais_iso3 is None
    assert incomplete_rows[0].anio is None


def test_sqlite_snapshot_opens_read_only_and_refuses_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    snapshot_dir = tmp_path / "snapshot"
    SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir)
    snapshot_path = snapshot_dir / "snapshot.sqlite"
    snapshot = SQLiteSnapshotRepository(snapshot_path)

    with pytest.raises(sqlite3.OperationalError):
        with snapshot.connection() as connection:
            connection.execute("DELETE FROM noticias")

    with pytest.raises(FileExistsError, match="ya existe"):
        SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir)


def test_sqlite_snapshot_cannot_be_written_inside_frozen_raw_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    snapshot_path = source / "raw" / "snapshot"

    with pytest.raises(ValueError, match="raw congelado"):
        SQLiteSnapshotRepository.create_from_directory(source, snapshot_path)


def test_copilot_uses_verified_sqlite_snapshot_for_offline_frozen_data(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    snapshot_dir = tmp_path / "snapshot"
    SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir)
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        RAW_DATA_DIR=tmp_path / "no-raw-data",
        MANIFEST_PATH=source / "manifest.json",
        SQLITE_SNAPSHOT_PATH=snapshot_dir / "snapshot.sqlite",
        SQLITE_DB_PATH=tmp_path / "missing-live.db",
        LLM_PROVIDER="mock",
        DECISION_PROVIDER="mock",
    )
    service = CopilotService(settings=settings, llm_client=MockLLMAdapter())

    news, count = service.load_corpus()

    assert count == 1
    assert news[0].id_noticia == "N-1"
    assert any(
        item.pais_iso3 == "PAN" and item.indicador_id == "NY.GDP.MKTP.KD.ZG" and item.anio == 2023
        for item in service.load_query_indicators()
    )
    assert service.load_query_events()[0].id == "us7000abcd"


def test_sqlite_snapshot_merges_recent_local_ingestion_without_review_state(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    operational_path = tmp_path / "operational.db"
    operational = SQLiteStorage(operational_path)
    operational.init_db()
    now = datetime(2026, 10, 9, tzinfo=timezone.utc)
    recent = now - timedelta(days=4)
    old = now - timedelta(days=100)
    operational.upsert_noticias(
        [
            {
                "id_noticia": "LIVE-RECENT",
                "titulo": "Noticia reciente GDELT",
                "url": "https://news.example/recent",
                "medio": "Medio GDELT",
                "fecha_publicacion": recent.isoformat(),
                "fecha_deteccion": recent.isoformat(),
            },
            {
                "id_noticia": "LIVE-OLD",
                "titulo": "Noticia fuera de ventana",
                "url": "https://news.example/old",
                "medio": "Medio GDELT",
                "fecha_publicacion": old.isoformat(),
                "fecha_deteccion": old.isoformat(),
            },
        ]
    )
    operational.upsert_indicadores(
        [
            {
                "pais_iso3": "PAN",
                "indicador_id": "NY.GDP.MKTP.KD.ZG",
                "anio": 2023,
                "valor": 7.5,
                "unidad": "%",
                "fuente_url": "https://api.worldbank.org/live",
            }
        ]
    )
    operational.upsert_eventos(
        [
            {
                "id": "live-earthquake",
                "magnitude": 4.5,
                "time": 1720000000000,
                "updated": 1720000001000,
                "longitud": -80.0,
                "latitud": 8.0,
                "profundidad": 11.0,
                "place": "Panama region",
                "url": "https://earthquake.usgs.gov/event/live-earthquake",
            }
        ]
    )

    snapshot = SQLiteSnapshotRepository.create_from_directory(
        source,
        tmp_path / "snapshot",
        operational_db_path=operational_path,
        now_utc=now,
    )

    assert {item.id_noticia for item in snapshot.load_noticias()} == {"N-1", "LIVE-RECENT"}
    indicators = snapshot.load_indicadores()
    assert (
        next(
            item
            for item in indicators
            if item.pais_iso3 == "PAN" and item.indicador_id == "NY.GDP.MKTP.KD.ZG" and item.anio == 2023
        ).valor
        == 7.5
    )
    assert len(indicators) == 540
    assert sum(item.valor is None for item in indicators) == 539
    assert {item.id for item in snapshot.load_eventos()} == {"us7000abcd", "live-earthquake"}
    assert snapshot.metadata()["source_live_content_sha256"]
    with snapshot.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM eventos").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM eventos_vivos").fetchone()[0] == 1
    assert not snapshot.has_table("fichas_casos")


@pytest.mark.parametrize("null_field", ["updated", "longitud", "latitud", "profundidad", "url", "status"])
def test_sqlite_snapshot_refuses_incompatible_usgs_nulls_without_publishing_a_partial_package(
    tmp_path: Path, null_field: str
) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    frozen_inputs = {path: path.read_bytes() for path in (source / "raw").iterdir()}
    frozen_inputs[source / "manifest.json"] = (source / "manifest.json").read_bytes()
    operational_path = tmp_path / "operational.db"
    operational = SQLiteStorage(operational_path)
    operational.init_db()
    complete = {
        "id": "USGS-COMPLETE",
        "magnitude": 4.5,
        "time": 1720000000000,
        "updated": 1720000001000,
        "longitud": -80.0,
        "latitud": 8.0,
        "profundidad": 11.0,
        "place": "Panama region",
        "url": "https://earthquake.usgs.gov/event/complete",
        "status": "reviewed",
    }
    incomplete = {**complete, "id": "USGS-INCOMPLETE", null_field: None}
    operational.upsert_eventos([complete, incomplete])
    snapshot_dir = tmp_path / "snapshot"

    with pytest.raises(ValueError, match="USGS-INCOMPLETE.*EventoGeoJSON"):
        SQLiteSnapshotRepository.create_from_directory(source, snapshot_dir, operational_db_path=operational_path)

    assert not snapshot_dir.exists()
    assert list(tmp_path.glob(".snapshot.*.partial")) == []
    assert all(path.read_bytes() == original for path, original in frozen_inputs.items())


def test_sqlite_snapshot_preserves_real_usgs_numeric_zeros(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _create_source_data(source)
    operational_path = tmp_path / "operational.db"
    operational = SQLiteStorage(operational_path)
    operational.init_db()
    # Write the stored observation directly: this test isolates snapshot conversion from live ingestion.
    with operational.get_connection() as connection:
        connection.execute(
            "INSERT INTO eventos_live "
            "(id, magnitude, time, updated, longitud, latitud, profundidad, place, status, url, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "USGS-ZERO",
                0.0,
                0,
                0,
                0.0,
                0.0,
                0.0,
                "Origen de coordenadas",
                "reviewed",
                "https://usgs.gov/zero",
                "2026-10-09",
            ),
        )

    snapshot = SQLiteSnapshotRepository.create_from_directory(
        source, tmp_path / "snapshot", operational_db_path=operational_path
    )

    event = next(item for item in snapshot.load_eventos() if item.id == "USGS-ZERO")
    assert (event.magnitude, event.time, event.updated, event.longitude, event.latitude, event.depth) == (
        0.0,
        0,
        0,
        0.0,
        0.0,
        0.0,
    )
