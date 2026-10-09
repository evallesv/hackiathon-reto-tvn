"""Build a challenge-compliant data snapshot in an isolated candidate directory."""

import csv
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hackiathon_reto_tvn.adapters.data.live_fetchers import LiveDataFetcher
from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.adapters.data.sqlite_snapshot import SQLiteSnapshotRepository
from hackiathon_reto_tvn.domain.snapshot_contract import SNAPSHOT_COUNTRIES, SNAPSHOT_INDICATORS
from hackiathon_reto_tvn.services.snapshot_audit import audit_snapshot

NEWS_FIELDS = (
    "id_noticia",
    "titulo",
    "url",
    "medio",
    "idioma",
    "fecha_publicacion",
    "fecha_deteccion",
    "fecha_extraccion",
    "tema",
    "origen",
    "alcance_texto",
)
INDICATOR_FIELDS = (
    "pais_iso3",
    "indicador_id",
    "anio",
    "valor",
    "unidad",
    "fuente_url",
    "fecha_extraccion",
    "licencia",
)
GDELT_QUERY = (
    "panama (economia OR logística OR turismo OR gobierno OR salud OR educación OR seguridad "
    "OR Canal OR infraestructura OR ambiente OR energía)"
)


def _validate_candidate_path(output_dir: Path) -> Path:
    candidate = output_dir.expanduser().resolve()
    repository_data = Path(__file__).resolve().parents[3] / "data"
    active_data = repository_data.resolve()
    raw_dir = (active_data / "raw").resolve()
    if candidate == active_data or candidate == raw_dir or active_data in candidate.parents:
        raise ValueError(f"La salida debe estar fuera del dataset activo congelado: {active_data}")
    if candidate == Path.home().resolve():
        raise ValueError("La carpeta de inicio no es una ubicación válida para el candidato")
    return candidate


async def _fetch_gdelt_complete(fetcher: LiveDataFetcher, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Split saturated 250-record GDELT windows into smaller serial requests."""
    request_count = 0

    async def fetch_window(window_start: datetime, window_end: datetime, depth: int = 0) -> list[dict[str, Any]]:
        nonlocal request_count
        request_count += 1
        if request_count > 64:
            raise RuntimeError("GDELT exceeded the 64-request safety limit while splitting saturated windows")

        results = await fetcher.fetch_gdelt(
            query=GDELT_QUERY,
            max_records=250,
            start_datetime=window_start.strftime("%Y%m%d%H%M%S"),
            end_datetime=window_end.strftime("%Y%m%d%H%M%S"),
        )
        if len(results) < 250:
            return results
        if depth >= 16 or window_end - window_start <= timedelta(minutes=1):
            raise RuntimeError("GDELT window remains saturated at its minimum supported interval")

        midpoint = window_start + (window_end - window_start) / 2
        # Overlap one second at the split and deduplicate URLs after collection.
        overlap = timedelta(seconds=1)
        left = await fetch_window(window_start, min(midpoint + overlap, window_end), depth + 1)
        right = await fetch_window(max(midpoint - overlap, window_start), window_end, depth + 1)
        return [*left, *right]

    return await fetch_window(start, end)


async def build_candidate_snapshot(output_dir: Path) -> dict[str, Any]:
    """Publish only a complete candidate; incomplete runs leave a report, not a snapshot."""
    candidate = _validate_candidate_path(output_dir)
    if candidate.exists():
        raise ValueError(f"El destino ya existe; elige una ruta nueva para no sobrescribirlo: {candidate}")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{candidate.name}.", suffix=".partial", dir=candidate.parent))
    raw_dir = stage / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=90)
    fetcher = LiveDataFetcher(timeout_seconds=15)
    source_errors: dict[str, str] = {}

    try:
        tvn = await fetcher.fetch_tvn_rss()
    except Exception as exc:
        tvn = []
        source_errors["tvn_rss"] = str(exc)
    try:
        gdelt_articles = await _fetch_gdelt_complete(fetcher, start, now)
    except Exception as exc:
        gdelt_articles = []
        source_errors["gdelt"] = str(exc)
    news_by_url: dict[str, dict[str, Any]] = {}
    for article in [*tvn, *gdelt_articles]:
        url = str(article.get("url", "")).strip()
        if url:
            news_by_url.setdefault(url, article)
    _write_csv(raw_dir / "noticias.csv", NEWS_FIELDS, list(news_by_url.values()))

    try:
        fetched_indicators = await fetcher.fetch_world_bank(
            countries=list(SNAPSHOT_COUNTRIES),
            indicators=list(SNAPSHOT_INDICATORS),
            start_year=2010,
            end_year=2024,
            strict=True,
        )
    except Exception as exc:
        fetched_indicators = []
        source_errors["world_bank"] = str(exc)
    _write_csv(raw_dir / "indicadores.csv", INDICATOR_FIELDS, fetched_indicators)

    try:
        usgs_events = await fetcher.fetch_usgs(
            min_magnitude=3.0,
            bbox=(5.0, 12.0, -86.0, -76.0),
            limit=20000,
            start_time="2024-01-01",
            end_time="2025-01-01",
        )
    except Exception as exc:
        usgs_events = []
        source_errors["usgs"] = str(exc)
    features = [
        {
            "type": "Feature",
            "id": event["id"],
            "properties": {
                "mag": event["magnitude"],
                "place": event["place"],
                "time": event["time"],
                "updated": event["updated"],
                "url": event["url"],
                "status": event["status"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [event["longitud"], event["latitud"], event["profundidad"]],
            },
        }
        for event in usgs_events
    ]
    (raw_dir / "eventos.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "metadata": {
                    "title": "USGS Earthquakes - Panama Region Box [5, 12] [-86, -76]",
                    "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
                    "generated": int(now.timestamp() * 1000),
                    "count": len(features),
                },
                "features": features,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    LocalStorageRepository().generate_manifest(stage)
    SQLiteSnapshotRepository.create_from_directory(stage, stage / "snapshot")
    report = audit_snapshot(stage)
    report["source_errors"] = source_errors
    report["ready"] = report["ready"] and not source_errors
    if report["ready"]:
        report["data_dir"] = str(candidate)
        (stage / "audit-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(stage, candidate)
    else:
        shutil.rmtree(stage)
        report["data_dir"] = str(candidate)
        report_path = candidate.with_name(f"{candidate.name}.audit-report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
