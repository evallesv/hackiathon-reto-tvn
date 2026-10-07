"""SQLite Storage Adapter for HackIAthon Copilot.

Provides persistent SQLite storage for periodic live data ingestion:
- Real news from TVN RSS and GDELT
- Macroeconomic indicators from the World Bank API
- Seismic event geojson data from the USGS API
- Ingestion execution audit logs

Designed to run on Fly.io mounted persistent volumes (e.g. /data/copilot.db)
or locally (data/storage/copilot.db).
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """Manages SQLite database schema, connections, and upsert operations."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a configured SQLite connection context with WAL mode."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS noticias_live (
                    id_noticia TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    medio TEXT,
                    idioma TEXT DEFAULT 'es',
                    fecha_publicacion TEXT,
                    fecha_deteccion TEXT,
                    fecha_extraccion TEXT,
                    tema TEXT,
                    origen TEXT,
                    alcance_texto TEXT DEFAULT 'titular_metadatos',
                    resumen TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_noticias_fecha_pub
                ON noticias_live(fecha_publicacion DESC);

                CREATE INDEX IF NOT EXISTS idx_noticias_origen
                ON noticias_live(origen);

                CREATE TABLE IF NOT EXISTS indicadores_live (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pais_iso3 TEXT NOT NULL,
                    indicador_id TEXT NOT NULL,
                    anio INTEGER NOT NULL,
                    valor REAL,
                    unidad TEXT,
                    fuente_url TEXT,
                    fecha_extraccion TEXT,
                    licencia TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(pais_iso3, indicador_id, anio)
                );

                CREATE INDEX IF NOT EXISTS idx_indicadores_pais
                ON indicadores_live(pais_iso3, anio DESC);

                CREATE TABLE IF NOT EXISTS eventos_live (
                    id TEXT PRIMARY KEY,
                    magnitude REAL NOT NULL,
                    place TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    updated INTEGER,
                    url TEXT,
                    latitud REAL,
                    longitud REAL,
                    profundidad REAL,
                    status TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_eventos_time
                ON eventos_live(time DESC);

                CREATE TABLE IF NOT EXISTS datasets_live (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset TEXT NOT NULL,
                    categoria TEXT,
                    titulo_dataset TEXT,
                    organizacion TEXT,
                    anio INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    resource_id TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    fecha_extraccion TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(resource_id, record_id)
                );

                CREATE INDEX IF NOT EXISTS idx_datasets_dataset
                ON datasets_live(dataset);

                CREATE INDEX IF NOT EXISTS idx_datasets_categoria
                ON datasets_live(categoria);

                CREATE TABLE IF NOT EXISTS ingestion_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fuente TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    registros_nuevos INTEGER DEFAULT 0,
                    detalles TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_ingestion_runs_time
                ON ingestion_runs(finished_at DESC);
            """)
        logger.info(f"SQLite database initialized at: {self.db_path}")

    def upsert_noticias(self, records: list[dict[str, Any]]) -> int:
        """Insert or update live news records, returning count of processed rows."""
        if not records:
            return 0

        now_utc = datetime.now(timezone.utc).isoformat()
        upsert_query = """
            INSERT INTO noticias_live (
                id_noticia, titulo, url, medio, idioma,
                fecha_publicacion, fecha_deteccion, fecha_extraccion,
                tema, origen, alcance_texto, resumen, metadata_json, created_at
            ) VALUES (
                :id_noticia, :titulo, :url, :medio, :idioma,
                :fecha_publicacion, :fecha_deteccion, :fecha_extraccion,
                :tema, :origen, :alcance_texto, :resumen, :metadata_json, :created_at
            )
            ON CONFLICT(url) DO UPDATE SET
                titulo = excluded.titulo,
                fecha_extraccion = excluded.fecha_extraccion,
                resumen = COALESCE(excluded.resumen, noticias_live.resumen),
                metadata_json = COALESCE(excluded.metadata_json, noticias_live.metadata_json);
        """
        processed = 0
        with self.get_connection() as conn:
            for rec in records:
                params = {
                    "id_noticia": rec.get("id_noticia") or f"NOT-LIVE-{abs(hash(rec.get('url', '')))}",
                    "titulo": rec.get("titulo", "Sin título"),
                    "url": rec.get("url", ""),
                    "medio": rec.get("medio", "Desconocido"),
                    "idioma": rec.get("idioma", "es"),
                    "fecha_publicacion": rec.get("fecha_publicacion", now_utc),
                    "fecha_deteccion": rec.get("fecha_deteccion", now_utc),
                    "fecha_extraccion": rec.get("fecha_extraccion", now_utc),
                    "tema": rec.get("tema", "general"),
                    "origen": rec.get("origen", "rss"),
                    "alcance_texto": rec.get("alcance_texto", "titular_metadatos"),
                    "resumen": rec.get("resumen", ""),
                    "metadata_json": json.dumps(rec.get("metadata", {})) if rec.get("metadata") else None,
                    "created_at": now_utc,
                }
                if params["url"]:
                    conn.execute(upsert_query, params)
                    processed += 1
        return processed

    def upsert_indicadores(self, records: list[dict[str, Any]]) -> int:
        """Insert or update indicator values, returning count of processed rows."""
        if not records:
            return 0

        now_utc = datetime.now(timezone.utc).isoformat()
        upsert_query = """
            INSERT INTO indicadores_live (
                pais_iso3, indicador_id, anio, valor, unidad,
                fuente_url, fecha_extraccion, licencia, created_at
            ) VALUES (
                :pais_iso3, :indicador_id, :anio, :valor, :unidad,
                :fuente_url, :fecha_extraccion, :licencia, :created_at
            )
            ON CONFLICT(pais_iso3, indicador_id, anio) DO UPDATE SET
                valor = excluded.valor,
                fecha_extraccion = excluded.fecha_extraccion,
                fuente_url = excluded.fuente_url;
        """
        processed = 0
        with self.get_connection() as conn:
            for rec in records:
                params = {
                    "pais_iso3": rec.get("pais_iso3", "PAN"),
                    "indicador_id": rec.get("indicador_id", ""),
                    "anio": int(rec.get("anio", 0)),
                    "valor": float(rec["valor"]) if rec.get("valor") is not None else None,
                    "unidad": rec.get("unidad", "%"),
                    "fuente_url": rec.get("fuente_url", ""),
                    "fecha_extraccion": rec.get("fecha_extraccion", now_utc),
                    "licencia": rec.get("licencia", "CC BY 4.0"),
                    "created_at": now_utc,
                }
                if params["indicador_id"] and params["anio"] > 0:
                    conn.execute(upsert_query, params)
                    processed += 1
        return processed

    def upsert_eventos(self, records: list[dict[str, Any]]) -> int:
        """Insert or update seismic events, returning count of processed rows."""
        if not records:
            return 0

        now_utc = datetime.now(timezone.utc).isoformat()
        upsert_query = """
            INSERT INTO eventos_live (
                id, magnitude, place, time, updated,
                url, latitud, longitud, profundidad, status, created_at
            ) VALUES (
                :id, :magnitude, :place, :time, :updated,
                :url, :latitud, :longitud, :profundidad, :status, :created_at
            )
            ON CONFLICT(id) DO UPDATE SET
                magnitude = excluded.magnitude,
                place = excluded.place,
                updated = excluded.updated,
                status = excluded.status;
        """
        processed = 0
        with self.get_connection() as conn:
            for rec in records:
                params = {
                    "id": rec.get("id", ""),
                    "magnitude": float(rec.get("magnitude", 0.0)),
                    "place": rec.get("place", "Región Panamá"),
                    "time": int(rec.get("time", 0)),
                    "updated": int(rec.get("updated", 0)) if rec.get("updated") else None,
                    "url": rec.get("url", ""),
                    "latitud": float(rec.get("latitud", 0.0)) if rec.get("latitud") is not None else None,
                    "longitud": float(rec.get("longitud", 0.0)) if rec.get("longitud") is not None else None,
                    "profundidad": float(rec.get("profundidad", 0.0)) if rec.get("profundidad") is not None else None,
                    "status": rec.get("status", "reviewed"),
                    "created_at": now_utc,
                }
                if params["id"]:
                    conn.execute(upsert_query, params)
                    processed += 1
        return processed

    def has_table(self, name: str) -> bool:
        """Return True if the table exists (lets standalone scripts fail clearly instead of creating schema)."""
        if not self.db_path.exists():
            return False
        with self.get_connection() as conn:
            row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
            return row is not None

    def replace_dataset_records(self, dataset: str, records: list[dict[str, Any]]) -> int:
        """Replace every stored row of an open-data dataset with the given records (one transaction).

        Each record carries `categoria`, `titulo_dataset`, `organizacion`, `anio`, `mes`, `resource_id`,
        `record_id` and `payload` (the raw row, nulls preserved). Replacing the whole dataset keeps stale rows from
        previous runs out of the table.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("DELETE FROM datasets_live WHERE dataset = ?", (dataset,))
            for rec in records:
                conn.execute(
                    """
                    INSERT INTO datasets_live (
                        dataset, categoria, titulo_dataset, organizacion, anio, mes,
                        resource_id, record_id, payload_json, fecha_extraccion, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        dataset,
                        rec.get("categoria"),
                        rec.get("titulo_dataset"),
                        rec.get("organizacion"),
                        int(rec["anio"]),
                        int(rec["mes"]),
                        rec["resource_id"],
                        int(rec["record_id"]),
                        json.dumps(rec["payload"], ensure_ascii=False),
                        now_utc,
                        now_utc,
                    ),
                )
        return len(records)

    def prune_datasets(self, keep: list[str]) -> int:
        """Delete rows of datasets that are not in `keep`, returning how many rows were removed."""
        with self.get_connection() as conn:
            if keep:
                marks = ",".join("?" * len(keep))
                cursor = conn.execute(f"DELETE FROM datasets_live WHERE dataset NOT IN ({marks})", keep)
            else:
                cursor = conn.execute("DELETE FROM datasets_live")
            return cursor.rowcount

    def record_run(
        self,
        fuente: str,
        estado: str,
        registros_nuevos: int,
        detalles: str,
        started_at: str,
        finished_at: str,
    ) -> None:
        """Log an ingestion execution event."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ingestion_runs (
                    fuente, estado, registros_nuevos, detalles, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (fuente, estado, registros_nuevos, detalles, started_at, finished_at),
            )

    def get_stats(self) -> dict[str, Any]:
        """Return counts of all tables and database size."""
        with self.get_connection() as conn:
            c_noticias = conn.execute("SELECT COUNT(*) FROM noticias_live").fetchone()[0]
            c_indicadores = conn.execute("SELECT COUNT(*) FROM indicadores_live").fetchone()[0]
            c_eventos = conn.execute("SELECT COUNT(*) FROM eventos_live").fetchone()[0]
            c_datasets = conn.execute("SELECT COUNT(*) FROM datasets_live").fetchone()[0]
            c_runs = conn.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]
            latest_run = conn.execute(
                "SELECT fuente, estado, registros_nuevos, finished_at FROM ingestion_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()

        db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "db_path": str(self.db_path),
            "db_size_bytes": db_size_bytes,
            "total_noticias": c_noticias,
            "total_indicadores": c_indicadores,
            "total_eventos": c_eventos,
            "total_datasets": c_datasets,
            "total_runs": c_runs,
            "latest_run": dict(latest_run) if latest_run else None,
        }

    def get_latest_noticias(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent live news items."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id_noticia, titulo, url, medio, idioma,
                       fecha_publicacion, tema, origen, resumen, created_at
                FROM noticias_live
                ORDER BY fecha_publicacion DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_latest_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent ingestion run logs."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, fuente, estado, registros_nuevos, detalles, started_at, finished_at
                FROM ingestion_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
