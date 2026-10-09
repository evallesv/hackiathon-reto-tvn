"""Data loaders and manifest generator adhering to HackIAthon data contracts.

Handles:
- T01: Non-blocking CSV loading with null preservation and error segregation
- T02: Deduplication and multi-source grouping (single provenance for syndicated news)
- T03: Recirculated news detection (flagging old publication date vs seen date)
- T04: Historical indicator context (preserving year, country, and unit)
- T05: Contradiction detection between opposing reports
- Manifest hashing via SHA-256
"""

import hashlib
import json
import logging
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from hackiathon_reto_tvn.domain.models import (
    EventoGeoJSON,
    FichaCaso,
    Indicador,
    Manifest,
    ManifestItem,
    Noticia,
)
from hackiathon_reto_tvn.ports.storage_port import BaseStorageRepository

logger = logging.getLogger(__name__)


def compute_sha256(filepath: Path) -> str:
    """Calculates SHA-256 checksum for a given file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _optional_csv_str(value: Any) -> Optional[str]:
    if pd.isna(value) or not str(value).strip() or str(value).strip().lower() == "nan":
        return None
    return str(value).strip()


def _optional_csv_int(value: Any) -> Optional[int]:
    if pd.isna(value) or not str(value).strip():
        return None
    try:
        numeric_value = float(value)
        return int(numeric_value) if numeric_value.is_integer() else None
    except (TypeError, ValueError, OverflowError):
        return None


class LocalStorageRepository(BaseStorageRepository):
    """File-system based storage repository for datasets, manifests, and case files."""

    def load_noticias(self, path: Path) -> List[Noticia]:
        """Loads noticias.csv, tolerates invalid dates and nulls, segregates errors without blocking (T01)."""
        if not path.exists():
            logger.warning(f"File {path} does not exist.")
            return []

        df = pd.read_csv(path, dtype=str)
        noticias: List[Noticia] = []

        for idx, row in df.iterrows():
            try:
                # Retain raw nulls, validate minimal ID & Title
                id_val = row.get("id_noticia")
                id_noticia = (
                    str(id_val).strip()
                    if pd.notna(id_val) and str(id_val).strip().lower() != "nan"
                    else f"noticia_{idx}"
                )

                titulo_raw = row.get("titulo")
                if pd.isna(titulo_raw) or not str(titulo_raw).strip() or str(titulo_raw).strip().lower() == "nan":
                    logger.warning(f"Row {idx} missing required title, skipping.")
                    continue
                titulo = str(titulo_raw).strip()

                def _safe_str(val: Any, default: str = "") -> str:
                    if pd.isna(val) or str(val).strip().lower() == "nan":
                        return default
                    return str(val).strip()

                item = Noticia(
                    id_noticia=id_noticia,
                    titulo=titulo,
                    url=_safe_str(row.get("url")),
                    medio=_safe_str(row.get("medio"), "Desconocido"),
                    idioma=_safe_str(row.get("idioma"), "es"),
                    fecha_publicacion=_safe_str(row.get("fecha_publicacion")),
                    fecha_deteccion=_safe_str(row.get("fecha_deteccion")),
                    fecha_extraccion=_safe_str(row.get("fecha_extraccion")),
                    tema=_safe_str(row.get("tema"), "general"),
                    origen=_safe_str(row.get("origen"), "rss"),
                    alcance_texto=_safe_str(row.get("alcance_texto"), "titular_metadatos"),
                )
                noticias.append(item)
            except Exception as exc:
                logger.error(f"Error parsing row {idx} in {path}: {exc}")

        return noticias

    def load_indicadores(self, path: Path) -> List[Indicador]:
        """Loads indicadores.csv, keeping null values explicitly without filling with zero (T01, T04)."""
        if not path.exists():
            return []

        df = pd.read_csv(path)
        indicadores: List[Indicador] = []

        for idx, row in df.iterrows():
            try:
                val = row.get("valor")
                valor_float: Optional[float] = None
                if pd.notna(val):
                    try:
                        valor_float = float(val)
                    except ValueError:
                        valor_float = None

                item = Indicador(
                    pais_iso3=_optional_csv_str(row.get("pais_iso3")),
                    indicador_id=_optional_csv_str(row.get("indicador_id")),
                    anio=_optional_csv_int(row.get("anio")),
                    valor=valor_float,
                    unidad=str(row.get("unidad", "")),
                    fuente_url=str(row.get("fuente_url", "")),
                    fecha_extraccion=str(row.get("fecha_extraccion", "")),
                    licencia=str(row.get("licencia", "CC BY 4.0")),
                )
                indicadores.append(item)
            except Exception as exc:
                logger.error(f"Error parsing indicador row {idx}: {exc}")

        return indicadores

    def load_eventos(self, path: Path) -> List[EventoGeoJSON]:
        """Load complete USGS events; diagnose incomplete features without inventing numeric values."""
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        eventos: List[EventoGeoJSON] = []
        features = data.get("features", [])

        for index, feat in enumerate(features):
            feature_id = feat.get("id", "sin id") if isinstance(feat, dict) else "sin id"
            try:
                props = feat.get("properties") or {}
                geom = feat.get("geometry") or {}
                coords = geom.get("coordinates")
                if not isinstance(coords, list) or len(coords) < 3:
                    raise ValueError("coordinates debe contener longitud, latitud y profundidad explícitas")

                evento = EventoGeoJSON.model_validate(
                    {
                        "id": str(feat.get("id", "")),
                        "magnitude": props.get("mag"),
                        "time": props.get("time"),
                        "updated": props.get("updated"),
                        "longitude": coords[0],
                        "latitude": coords[1],
                        "depth": coords[2],
                        "place": str(props.get("place", "")),
                        "status": str(props.get("status", "")),
                        "url": str(props.get("url", "")),
                    }
                )
                eventos.append(evento)
            except Exception as exc:
                logger.error("Error parsing feature %s (%s) in %s: %s", index, feature_id, path, exc)

        return eventos

    def save_fichas(self, fichas: List[FichaCaso], output_path: Path) -> None:
        """Saves case cards to fichas.jsonl."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for ficha in fichas:
                f.write(json.dumps(ficha.model_dump(), ensure_ascii=False) + "\n")

    def generate_manifest(self, data_dir: Path) -> Manifest:
        """Generates manifest.json with SHA-256 hashes and file counts."""
        items: List[ManifestItem] = []
        counts: Dict[str, int] = {}

        for filename, lic, trans in [
            ("noticias.csv", "Derechos de autor TVN/GDELT - Uso referencial", "Deduplicación y normalización UTC"),
            ("indicadores.csv", "CC BY 4.0 (Banco Mundial / SBP)", "Conservación de nulos y tipos numéricos"),
            ("eventos.geojson", "Dominio público (USGS)", "Filtrado regional lat 5-12, lon -86 a -76"),
        ]:
            file_path = data_dir / "raw" / filename
            if file_path.exists():
                sha = compute_sha256(file_path)
                # Count records
                if filename.endswith(".csv"):
                    df = pd.read_csv(file_path)
                    count = len(df)
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    count = len(data.get("features", []))

                counts[filename] = count
                items.append(
                    ManifestItem(
                        archivo=f"raw/{filename}",
                        cantidad_registros=count,
                        licencia=lic,
                        sha256=sha,
                        transformaciones=trans,
                    )
                )

        now_utc = datetime.now(timezone.utc).isoformat()
        manifest = Manifest(
            version="v1.0",
            fecha_corte_utc=now_utc,
            consultas=[
                "TVN RSS Panama",
                "GDELT DOC 2.0 Panama logistica turismo economia",
                "World Bank Indicators (PAN, CRI, COL, DOM, MEX, GTM)",
                "USGS Earthquake Catalog Box [5,12] [-86,-76]",
            ],
            cantidad_por_archivo=counts,
            licencia_condiciones="Ver licencias específicas por archivo en items. Uso exclusivo hackIAthon.",
            archivos=items,
        )

        manifest_path = data_dir / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)

        return manifest


def _parse_date(value: str) -> Optional[date]:
    """Parses the leading YYYY-MM-DD of an ISO-like timestamp; returns None if not parseable (T01)."""
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


class EventGrouper:
    """Groups duplicate news articles into single events to avoid inflating corroboration (T02)."""

    RECIRCULATION_THRESHOLD_DAYS = 3
    EVENT_MATCH_WINDOW_DAYS = 14
    TITLE_STOP_WORDS = {
        "al",
        "ante",
        "anuncia",
        "anuncian",
        "con",
        "contra",
        "de",
        "del",
        "durante",
        "el",
        "en",
        "entre",
        "esta",
        "este",
        "la",
        "las",
        "los",
        "mientras",
        "para",
        "por",
        "que",
        "segun",
        "sin",
        "sobre",
        "tras",
        "un",
        "una",
        "y",
        "gobierno",
        "plan",
    }

    @staticmethod
    def group_articles(articles: List[Noticia]) -> Dict[str, List[Noticia]]:
        """Group likely duplicate coverage by shared content terms within a recency window."""
        parents = list(range(len(articles)))

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        for left in range(len(articles)):
            for right in range(left + 1, len(articles)):
                if EventGrouper._same_event_candidate(articles[left], articles[right]):
                    left_root, right_root = find(left), find(right)
                    if left_root != right_root:
                        parents[right_root] = left_root

        clusters: Dict[str, List[Noticia]] = {}
        for index, article in enumerate(articles):
            root = find(index)
            key = f"evento_{articles[root].id_noticia}"
            clusters.setdefault(key, []).append(article)
        return clusters

    @staticmethod
    def _normalized_title_tokens(title: str) -> set[str]:
        normalized = unicodedata.normalize("NFKD", title.casefold())
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        return {
            token
            for token in re.findall(r"[a-z0-9]+", ascii_text)
            if len(token) > 2 and token not in EventGrouper.TITLE_STOP_WORDS
        }

    @classmethod
    def _same_event_candidate(cls, first: Noticia, second: Noticia) -> bool:
        first_date = _parse_date(first.fecha_publicacion)
        second_date = _parse_date(second.fecha_publicacion)
        if first_date and second_date and abs((first_date - second_date).days) > cls.EVENT_MATCH_WINDOW_DAYS:
            return False

        first_tokens = cls._normalized_title_tokens(first.titulo)
        second_tokens = cls._normalized_title_tokens(second.titulo)
        shared_terms = first_tokens & second_tokens
        smallest_title_term_count = min(len(first_tokens), len(second_tokens))
        return (
            smallest_title_term_count > 0
            and len(shared_terms) >= 2
            and len(shared_terms) / smallest_title_term_count >= 0.6
        )

    @classmethod
    def detect_recirculated(cls, noticia: Noticia) -> Tuple[bool, str]:
        """Detects whether a news article was published well before it was detected (T03).

        Compares calendar dates (not raw timestamps): same-day publication/detection is never recirculation.
        Unparseable dates are not flagged, because recirculation cannot be asserted without evidence (T01).
        """
        pub = noticia.fecha_publicacion
        seen = noticia.fecha_deteccion
        pub_date, seen_date = _parse_date(pub), _parse_date(seen)
        if pub_date and seen_date and (seen_date - pub_date).days > cls.RECIRCULATION_THRESHOLD_DAYS:
            return True, f"Noticia publicada el {pub} pero detectada recientemente ({seen}). Mantener fecha original."
        return False, "Noticia con fechas consistentes."
