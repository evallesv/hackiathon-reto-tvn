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

                CREATE TABLE IF NOT EXISTS fichas_casos (
                    id_caso TEXT PRIMARY KEY,
                    modalidad TEXT NOT NULL DEFAULT 'tvn_editorial',
                    titulo_caso TEXT NOT NULL,
                    score_atencion REAL NOT NULL,
                    banda_prioridad TEXT NOT NULL,
                    estado_evidencia TEXT NOT NULL,
                    estado_revision TEXT NOT NULL DEFAULT 'en_revision',
                    persona_revisora TEXT,
                    observaciones_revision TEXT,
                    ficha_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_fichas_score
                ON fichas_casos(score_atencion DESC);

                CREATE INDEX IF NOT EXISTS idx_fichas_estado_rev
                ON fichas_casos(estado_revision);
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
            c_runs = conn.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]
            c_fichas = conn.execute("SELECT COUNT(*) FROM fichas_casos").fetchone()[0]
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
            "total_runs": c_runs,
            "total_fichas": c_fichas,
            "latest_run": dict(latest_run) if latest_run else None,
        }

    def upsert_ficha(self, ficha: dict[str, Any] | Any) -> None:
        """Insert or update a FichaCaso in SQLite."""
        if hasattr(ficha, "model_dump"):
            data = ficha.model_dump()
        elif isinstance(ficha, dict):
            data = dict(ficha)
        else:
            raise ValueError("Ficha debe ser dict o modelo Pydantic")

        now_utc = datetime.now(timezone.utc).isoformat()
        id_caso = str(data.get("id_caso", ""))
        modalidad = str(data.get("modalidad", "tvn_editorial"))
        borrador = data.get("borrador") or {}
        afirmaciones = data.get("afirmaciones") or []
        titulo = (
            borrador.get("titulo_propuesto")
            or borrador.get("resumen_250")
            or (afirmaciones[0].get("texto") if afirmaciones else None)
            or f"Caso {id_caso}"
        )
        if len(titulo) > 120:
            titulo = titulo[:117] + "..."

        score = float(data.get("puntaje", 0.0))
        banda = "Alto" if score >= 70.0 else ("Medio" if score >= 40.0 else "Bajo")
        estado_evidencia = str(data.get("estado_evidencia", "insuficiente"))
        estado_revision = str(data.get("estado_revision", "en_revision"))
        persona_revisora = data.get("persona_revisora")
        observaciones_revision = data.get("observaciones_revision")
        created_at = str(data.get("fecha_creacion") or now_utc)

        ficha_json = json.dumps(data, ensure_ascii=False)

        upsert_query = """
            INSERT INTO fichas_casos (
                id_caso, modalidad, titulo_caso, score_atencion, banda_prioridad,
                estado_evidencia, estado_revision, persona_revisora,
                observaciones_revision, ficha_json, created_at, updated_at
            ) VALUES (
                :id_caso, :modalidad, :titulo_caso, :score_atencion, :banda_prioridad,
                :estado_evidencia, :estado_revision, :persona_revisora,
                :observaciones_revision, :ficha_json, :created_at, :updated_at
            )
            ON CONFLICT(id_caso) DO UPDATE SET
                modalidad = excluded.modalidad,
                titulo_caso = excluded.titulo_caso,
                score_atencion = excluded.score_atencion,
                banda_prioridad = excluded.banda_prioridad,
                estado_evidencia = excluded.estado_evidencia,
                estado_revision = excluded.estado_revision,
                persona_revisora = excluded.persona_revisora,
                observaciones_revision = excluded.observaciones_revision,
                ficha_json = excluded.ficha_json,
                updated_at = excluded.updated_at;
        """
        params = {
            "id_caso": id_caso,
            "modalidad": modalidad,
            "titulo_caso": titulo,
            "score_atencion": score,
            "banda_prioridad": banda,
            "estado_evidencia": estado_evidencia,
            "estado_revision": estado_revision,
            "persona_revisora": persona_revisora,
            "observaciones_revision": observaciones_revision,
            "ficha_json": ficha_json,
            "created_at": created_at,
            "updated_at": now_utc,
        }
        with self.get_connection() as conn:
            conn.execute(upsert_query, params)

    def get_ficha(self, id_caso: str) -> dict[str, Any] | None:
        """Retrieve a single case by id."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT ficha_json FROM fichas_casos WHERE id_caso = ?",
                (id_caso,),
            ).fetchone()
            if row:
                res: dict[str, Any] = json.loads(row["ficha_json"])
                return res
            return None

    def get_all_fichas(self) -> list[dict[str, Any]]:
        """Retrieve all cases ordered by attention score descending."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT ficha_json FROM fichas_casos ORDER BY score_atencion DESC").fetchall()
            return [json.loads(r["ficha_json"]) for r in rows]

    def update_review_status(
        self,
        id_caso: str,
        nuevo_estado: str,
        persona_revisora: str | None = None,
        observaciones: str | None = None,
    ) -> dict[str, Any] | None:
        """Update review state, reviewer, and notes for a case."""
        existing = self.get_ficha(id_caso)
        if not existing:
            return None

        existing["estado_revision"] = nuevo_estado
        if persona_revisora:
            existing["persona_revisora"] = persona_revisora
        if observaciones is not None:
            existing["observaciones_revision"] = observaciones

        self.upsert_ficha(existing)
        return existing

    def seed_fichas_from_jsonl(self, jsonl_path: Path | str) -> int:
        """Seed SQLite database from a fichas.jsonl file."""
        path = Path(jsonl_path)
        if not path.exists():
            return 0

        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                self.upsert_ficha(data)
                count += 1
        return count

    def get_latest_noticias(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent live news items."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id_noticia, titulo, url, medio, idioma,
                       fecha_publicacion, fecha_deteccion, fecha_extraccion,
                       tema, origen, alcance_texto, resumen, created_at
                FROM noticias_live
                ORDER BY COALESCE(NULLIF(fecha_publicacion, ''), fecha_deteccion) DESC
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
