"""Create and read immutable SQLite packages of the frozen public-data corpus."""

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator

from pydantic import ValidationError

from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.domain.models import EventoGeoJSON, Indicador, Noticia
from hackiathon_reto_tvn.domain.snapshot_contract import EXPECTED_INDICATOR_KEYS, INDICATOR_UNITS

SNAPSHOT_SCHEMA_VERSION = 1


class SQLiteSnapshotRepository:
    """Read-only adapter for a portable snapshot, separate from mutable operational SQLite state."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path).expanduser().resolve()

    @classmethod
    def create_from_directory(
        cls,
        data_dir: Path,
        snapshot_dir: Path,
        operational_db_path: Path | None = None,
        now_utc: datetime | None = None,
        live_window_days: int = 90,
    ) -> "SQLiteSnapshotRepository":
        """Package raw CSV/GeoJSON records in an atomic, self-contained SQLite snapshot directory."""
        source_dir = data_dir.expanduser().resolve()
        destination = snapshot_dir.expanduser().resolve()
        raw_dir = (source_dir / "raw").resolve()
        if destination == raw_dir or raw_dir in destination.parents:
            raise ValueError(f"La salida no puede escribirse dentro de raw congelado: {raw_dir}")
        if destination.exists():
            raise FileExistsError(f"El snapshot ya existe; usa una nueva ruta versionada: {destination}")
        if not (source_dir / "manifest.json").is_file():
            raise FileNotFoundError(f"No existe el manifiesto de origen: {source_dir / 'manifest.json'}")

        source_manifest_bytes = (source_dir / "manifest.json").read_bytes()
        source_hash = hashlib.sha256(source_manifest_bytes).hexdigest()
        manifest = json.loads(source_manifest_bytes)
        repository = LocalStorageRepository()
        noticias = repository.load_noticias(raw_dir / "noticias.csv")
        indicadores = repository.load_indicadores(raw_dir / "indicadores.csv")
        eventos = repository.load_eventos(raw_dir / "eventos.geojson")
        snapshot_time = now_utc or datetime.now(timezone.utc)
        live_records = _read_recent_operational_records(
            operational_db_path,
            snapshot_time - timedelta(days=live_window_days),
        )
        noticias = _merge_news(noticias, live_records["noticias"])
        indicadores = _complete_indicator_grid(
            _merge_indicators(indicadores, live_records["indicadores"]),
            snapshot_time.isoformat(),
        )
        counts = {
            "eventos": len(eventos),
            "eventos_vivos": len(live_records["eventos"]),
            "indicadores": len(indicadores),
            "noticias": len(noticias),
        }

        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", suffix=".partial", dir=destination.parent))
        database_path = stage / "snapshot.sqlite"
        try:
            _write_snapshot_database(
                database_path,
                noticias,
                indicadores,
                eventos,
                live_records["eventos"],
                {
                    "schema_version": SNAPSHOT_SCHEMA_VERSION,
                    "fecha_corte_utc": snapshot_time.isoformat(),
                    "source_manifest_cutoff_utc": str(manifest.get("fecha_corte_utc", "")),
                    "source_manifest_sha256": source_hash,
                    "source_live_content_sha256": live_records["sha256"],
                    "source_live_content_counts": live_records["counts"],
                    "counts": counts,
                    "indicator_grid": {
                        "expected_combinations": len(EXPECTED_INDICATOR_KEYS),
                        "populated_values": sum(item.valor is not None for item in indicadores),
                        "null_values": sum(item.valor is None for item in indicadores),
                        "missing_values_are_null_not_imputed": True,
                    },
                },
            )
            snapshot_manifest = {
                "schema_version": SNAPSHOT_SCHEMA_VERSION,
                "snapshot_file": "snapshot.sqlite",
                "snapshot_sha256": _sha256_file(database_path),
                "fecha_corte_utc": snapshot_time.isoformat(),
                "source_manifest_sha256": source_hash,
                "source_live_content_sha256": live_records["sha256"],
                "source_live_content_counts": live_records["counts"],
                "counts": counts,
                "indicator_grid": {
                    "expected_combinations": len(EXPECTED_INDICATOR_KEYS),
                    "populated_values": sum(item.valor is not None for item in indicadores),
                    "null_values": sum(item.valor is None for item in indicadores),
                    "missing_values_are_null_not_imputed": True,
                },
                "included_tables": [
                    "noticias",
                    "indicadores",
                    "eventos",
                    "eventos_vivos",
                    "snapshot_metadata",
                ],
                "excluded_tables": ["fichas_casos", "ingestion_runs"],
                "operational_ingestion_included": any(live_records["counts"].values()),
            }
            (stage / "snapshot_manifest.json").write_text(
                json.dumps(snapshot_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            os.replace(stage, destination)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        return cls(destination / "snapshot.sqlite")

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Open the snapshot read-only so a demo cannot mutate the frozen corpus."""
        if not self.database_path.is_file():
            raise FileNotFoundError(self.database_path)
        connection = sqlite3.connect(f"{self.database_path.as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def load_noticias(self) -> list[Noticia]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_deteccion, "
                "fecha_extraccion, tema, origen, alcance_texto FROM noticias ORDER BY id_noticia"
            ).fetchall()
        return [Noticia.model_validate(dict(row)) for row in rows]

    def load_indicadores(self) -> list[Indicador]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT pais_iso3, indicador_id, anio, valor, unidad, fuente_url, fecha_extraccion, licencia "
                "FROM indicadores ORDER BY pais_iso3, indicador_id, anio"
            ).fetchall()
        return [Indicador.model_validate(dict(row)) for row in rows]

    def load_eventos(self) -> list[EventoGeoJSON]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id, magnitude, time, updated, longitude, latitude, depth, place, status, url "
                "FROM eventos ORDER BY time DESC, id"
            ).fetchall()
            live_rows = connection.execute(
                "SELECT id, magnitude, time, updated, longitude, latitude, depth, place, status, url "
                "FROM eventos_vivos ORDER BY time DESC, id"
            ).fetchall()
        frozen = [EventoGeoJSON.model_validate(dict(row)) for row in rows]
        live = [EventoGeoJSON.model_validate(dict(row)) for row in live_rows]
        return _merge_events(frozen, live)

    def metadata(self) -> dict[str, Any]:
        with self.connection() as connection:
            rows = connection.execute("SELECT clave, valor_json FROM snapshot_metadata").fetchall()
        return {row["clave"]: json.loads(row["valor_json"]) for row in rows}

    def is_valid_for_manifest(self, source_manifest_path: Path) -> bool:
        """Reject snapshots whose source manifest or packaged database has changed."""
        manifest_path = self.database_path.parent / "snapshot_manifest.json"
        try:
            package_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            source_hash = _sha256_file(source_manifest_path)
            metadata = self.metadata()
            return (
                package_manifest.get("schema_version") == SNAPSHOT_SCHEMA_VERSION
                and package_manifest.get("snapshot_sha256") == _sha256_file(self.database_path)
                and package_manifest.get("source_manifest_sha256") == source_hash
                and metadata.get("schema_version") == SNAPSHOT_SCHEMA_VERSION
                and metadata.get("source_manifest_sha256") == source_hash
            )
        except (OSError, sqlite3.Error, json.JSONDecodeError, ValueError):
            return False

    def has_table(self, table_name: str) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
            ).fetchone()
        return row is not None


def _write_snapshot_database(
    path: Path,
    noticias: list[Noticia],
    indicadores: list[Indicador],
    eventos: list[EventoGeoJSON],
    eventos_vivos: list[EventoGeoJSON],
    metadata: dict[str, Any],
) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            PRAGMA synchronous=FULL;
            CREATE TABLE snapshot_metadata (clave TEXT PRIMARY KEY, valor_json TEXT NOT NULL);
            CREATE TABLE noticias (
                id_noticia TEXT PRIMARY KEY, titulo TEXT NOT NULL, url TEXT NOT NULL, medio TEXT NOT NULL,
                idioma TEXT NOT NULL, fecha_publicacion TEXT NOT NULL, fecha_deteccion TEXT NOT NULL,
                fecha_extraccion TEXT NOT NULL, tema TEXT NOT NULL, origen TEXT NOT NULL, alcance_texto TEXT NOT NULL
            );
            CREATE INDEX idx_snapshot_noticias_fecha ON noticias(fecha_publicacion DESC);
            CREATE TABLE indicadores (
                pais_iso3 TEXT, indicador_id TEXT, anio INTEGER, valor REAL,
                unidad TEXT NOT NULL, fuente_url TEXT NOT NULL, fecha_extraccion TEXT NOT NULL, licencia TEXT NOT NULL,
                PRIMARY KEY (pais_iso3, indicador_id, anio)
            );
            CREATE TABLE eventos (
                id TEXT PRIMARY KEY, magnitude REAL NOT NULL, time INTEGER NOT NULL, updated INTEGER NOT NULL,
                longitude REAL NOT NULL, latitude REAL NOT NULL, depth REAL NOT NULL, place TEXT NOT NULL,
                status TEXT NOT NULL, url TEXT NOT NULL
            );
            CREATE INDEX idx_snapshot_eventos_time ON eventos(time DESC);
            CREATE TABLE eventos_vivos (
                id TEXT PRIMARY KEY, magnitude REAL NOT NULL, time INTEGER NOT NULL, updated INTEGER NOT NULL,
                longitude REAL NOT NULL, latitude REAL NOT NULL, depth REAL NOT NULL, place TEXT NOT NULL,
                status TEXT NOT NULL, url TEXT NOT NULL
            );
            CREATE INDEX idx_snapshot_eventos_vivos_time ON eventos_vivos(time DESC);
            """
        )
        connection.executemany(
            "INSERT INTO snapshot_metadata (clave, valor_json) VALUES (?, ?)",
            [(key, json.dumps(value, ensure_ascii=False, sort_keys=True)) for key, value in metadata.items()],
        )
        connection.executemany(
            "INSERT INTO noticias VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(item.model_dump().values()) for item in noticias],
        )
        connection.executemany(
            "INSERT INTO indicadores VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(item.model_dump().values()) for item in indicadores],
        )
        connection.executemany(
            "INSERT INTO eventos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(item.model_dump().values()) for item in eventos],
        )
        connection.executemany(
            "INSERT INTO eventos_vivos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(item.model_dump().values()) for item in eventos_vivos],
        )
        connection.commit()
    finally:
        connection.close()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _read_recent_operational_records(
    database_path: Path | None,
    cutoff: datetime,
) -> dict[str, Any]:
    if database_path is None or not database_path.is_file():
        empty_content: dict[str, list[Any]] = {"noticias": [], "indicadores": [], "eventos": []}
        return {
            **empty_content,
            "counts": dict.fromkeys(empty_content, 0),
            "sha256": hashlib.sha256(b"[]").hexdigest(),
        }

    source = database_path.expanduser().resolve()
    uri = f"{source.as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        tables = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        connection.execute("BEGIN")
        if not {"noticias_live", "indicadores_live", "eventos_live"}.issubset(tables):
            raise ValueError(f"La base operacional no tiene el esquema esperado: {source}")
        news_rows = connection.execute(
            "SELECT id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_deteccion, "
            "fecha_extraccion, tema, origen, alcance_texto FROM noticias_live"
        ).fetchall()
        indicator_rows = connection.execute(
            "SELECT pais_iso3, indicador_id, anio, valor, unidad, fuente_url, fecha_extraccion, licencia "
            "FROM indicadores_live"
        ).fetchall()
        event_rows = connection.execute(
            "SELECT id, magnitude, time, updated, longitud, latitud, profundidad, place, status, url FROM eventos_live"
        ).fetchall()

    noticias: list[Noticia] = []
    for row in news_rows:
        item = dict(row)
        published = _parse_datetime(item.get("fecha_publicacion")) or _parse_datetime(item.get("fecha_deteccion"))
        if published is None or published < cutoff:
            continue
        noticias.append(Noticia.model_validate(item))
    indicadores = [Indicador.model_validate(dict(row)) for row in indicator_rows]
    eventos: list[EventoGeoJSON] = []
    for row in event_rows:
        try:
            evento = EventoGeoJSON.model_validate(
                {
                    "id": row["id"],
                    "magnitude": row["magnitude"],
                    "time": row["time"],
                    "updated": row["updated"],
                    "longitude": row["longitud"],
                    "latitude": row["latitud"],
                    "depth": row["profundidad"],
                    "place": row["place"],
                    "status": row["status"],
                    "url": row["url"],
                }
            )
        except ValidationError as exc:
            raise ValueError(
                f"No se puede publicar el snapshot: evento USGS '{row['id']}' incompatible con EventoGeoJSON: {exc}"
            ) from exc
        eventos.append(evento)
    canonical = {
        "noticias": [item.model_dump() for item in noticias],
        "indicadores": [item.model_dump() for item in indicadores],
        "eventos": [item.model_dump() for item in eventos],
    }
    serialized = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "noticias": noticias,
        "indicadores": indicadores,
        "eventos": eventos,
        "counts": {key: len(value) for key, value in canonical.items()},
        "sha256": hashlib.sha256(serialized).hexdigest(),
    }


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _merge_news(frozen: list[Noticia], live: list[Noticia]) -> list[Noticia]:
    merged = {item.url: item for item in frozen if item.url}
    merged.update({item.url: item for item in live if item.url})
    return sorted(merged.values(), key=lambda item: item.id_noticia)


def _merge_indicators(frozen: list[Indicador], live: list[Indicador]) -> list[Indicador]:
    merged = {(item.pais_iso3, item.indicador_id, item.anio): item for item in frozen}
    merged.update({(item.pais_iso3, item.indicador_id, item.anio): item for item in live})
    return sorted(
        merged.values(),
        key=lambda item: (item.pais_iso3 or "", item.indicador_id or "", item.anio if item.anio is not None else -1),
    )


def _complete_indicator_grid(indicators: list[Indicador], extracted_at: str) -> list[Indicador]:
    """Represent absent World Bank combinations as explicit null rows without inventing values."""
    merged = {(item.pais_iso3, item.indicador_id, item.anio): item for item in indicators}
    for country, indicator, year in EXPECTED_INDICATOR_KEYS - merged.keys():
        merged[(country, indicator, year)] = Indicador(
            pais_iso3=country,
            indicador_id=indicator,
            anio=year,
            valor=None,
            unidad=INDICATOR_UNITS[indicator],
            fuente_url=(
                f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date={year}&format=json"
            ),
            fecha_extraccion=extracted_at,
            licencia="CC BY 4.0",
        )
    return sorted(
        merged.values(),
        key=lambda item: (item.pais_iso3 or "", item.indicador_id or "", item.anio if item.anio is not None else -1),
    )


def _merge_events(frozen: list[EventoGeoJSON], live: list[EventoGeoJSON]) -> list[EventoGeoJSON]:
    merged = {item.id: item for item in frozen}
    merged.update({item.id: item for item in live})
    return sorted(merged.values(), key=lambda item: (item.time, item.id), reverse=True)
