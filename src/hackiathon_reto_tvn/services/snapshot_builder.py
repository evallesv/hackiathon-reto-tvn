"""Build a challenge-compliant data snapshot in an isolated candidate directory."""

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hackiathon_reto_tvn.adapters.data.live_fetchers import LiveDataFetcher
from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.services.snapshot_audit import COUNTRIES, INDICATOR_YEARS, INDICATORS, audit_snapshot

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
GDELT_QUERIES = (
    "panama (economia OR logística OR turismo OR gobierno OR salud OR educación OR seguridad "
    "OR Canal OR infraestructura OR ambiente OR energía)",
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


async def build_candidate_snapshot(output_dir: Path) -> dict[str, Any]:
    """Fetch source data and write an auditable candidate without touching ``data/``."""
    candidate = _validate_candidate_path(output_dir)
    raw_dir = candidate / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=90)
    start_gdelt = start.strftime("%Y%m%d%H%M%S")
    end_gdelt = now.strftime("%Y%m%d%H%M%S")
    fetcher = LiveDataFetcher(timeout_seconds=15)
    source_errors: dict[str, str] = {}

    try:
        tvn = await fetcher.fetch_tvn_rss()
    except Exception as exc:
        tvn = []
        source_errors["tvn_rss"] = str(exc)
    try:
        gdelt_batches = [
            await fetcher.fetch_gdelt(
                query=GDELT_QUERIES[0],
                max_records=250,
                start_datetime=start_gdelt,
                end_datetime=end_gdelt,
            )
        ]
    except Exception as exc:
        gdelt_batches = []
        source_errors["gdelt"] = str(exc)
    news_by_url: dict[str, dict[str, Any]] = {}
    for article in [*tvn, *(item for batch in gdelt_batches for item in batch)]:
        url = str(article.get("url", "")).strip()
        if url:
            news_by_url.setdefault(url, article)
    _write_csv(raw_dir / "noticias.csv", NEWS_FIELDS, list(news_by_url.values()))

    try:
        fetched_indicators = await fetcher.fetch_world_bank(
            countries=list(COUNTRIES), indicators=list(INDICATORS), start_year=2010, end_year=2024
        )
    except Exception as exc:
        fetched_indicators = []
        source_errors["world_bank"] = str(exc)
    indicator_by_key = {
        (str(row["pais_iso3"]), str(row["indicador_id"]), int(row["anio"])): row
        for row in fetched_indicators
        if row.get("anio") is not None
    }
    extraction_time = datetime.now(timezone.utc).isoformat()
    indicators: list[dict[str, Any]] = []
    for country in COUNTRIES:
        for indicator in INDICATORS:
            for year in INDICATOR_YEARS:
                row = indicator_by_key.get((country, indicator, year))
                if row is None:
                    row = {
                        "pais_iso3": country,
                        "indicador_id": indicator,
                        "anio": year,
                        "valor": None,
                        "unidad": "personas" if indicator == "SP.POP.TOTL" else "%",
                        "fuente_url": (f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"),
                        "fecha_extraccion": extraction_time,
                        "licencia": "CC BY 4.0 (Banco Mundial)",
                    }
                indicators.append(row)
    _write_csv(raw_dir / "indicadores.csv", INDICATOR_FIELDS, indicators)

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

    LocalStorageRepository().generate_manifest(candidate)
    report = audit_snapshot(candidate)
    report["source_errors"] = source_errors
    report["ready"] = report["ready"] and not source_errors
    (candidate / "audit-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
