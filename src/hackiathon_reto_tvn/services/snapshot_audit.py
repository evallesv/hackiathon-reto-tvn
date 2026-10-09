"""Read-only compliance audit for proposed HackIAthon public-data snapshots."""

import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from itertools import product
from pathlib import Path
from typing import Any

COUNTRIES = ("PAN", "CRI", "COL", "DOM", "MEX", "GTM")
INDICATORS = (
    "NY.GDP.MKTP.KD.ZG",
    "FP.CPI.TOTL.ZG",
    "SL.UEM.TOTL.ZS",
    "SP.POP.TOTL",
    "IT.NET.USER.ZS",
    "NE.EXP.GNFS.ZS",
)
INDICATOR_YEARS = range(2010, 2025)
EXPECTED_INDICATOR_KEYS = set(product(COUNTRIES, INDICATORS, INDICATOR_YEARS))
USGS_START = date(2024, 1, 1)
USGS_END = date(2025, 1, 1)


def audit_snapshot(data_dir: Path) -> dict[str, Any]:
    """Check the challenge minimums without writing to the candidate snapshot."""
    manifest_path = data_dir / "manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    cutoff_date = _manifest_cutoff(manifest)

    news = _audit_news(data_dir / "raw" / "noticias.csv", cutoff_date)
    indicators = _audit_indicators(data_dir / "raw" / "indicadores.csv")
    usgs = _audit_usgs(data_dir / "raw" / "eventos.geojson")
    manifest_audit = _audit_manifest(data_dir, manifest)

    checks = {
        "news_minimum": news["within_90_days"] >= 100 and news["tvn_within_90_days"] >= 20,
        "indicator_grid": indicators["covered_combinations"] == 540 and indicators["duplicate_keys"] == 0,
        "usgs_scope": usgs["invalid_events"] == 0,
        "manifest_hashes": manifest_audit["valid"],
    }
    return {
        "data_dir": str(data_dir),
        "cutoff_date": cutoff_date.isoformat(),
        "ready": all(checks.values()),
        "checks": checks,
        "news": news,
        "indicators": indicators,
        "usgs": usgs,
        "manifest": manifest_audit,
        "notes": [
            "La cuadrícula del PDF tiene 6 países x 6 indicadores x 15 años = 540 combinaciones; el valor 1,350 indicado allí no coincide con esos ejes.",
            "Esta auditoría comprueba estructura y alcance, no licencias por registro, calidad editorial ni pertinencia semántica.",
        ],
    }


def _audit_news(path: Path, cutoff: date) -> dict[str, Any]:
    rows = _read_csv(path)
    start_30 = cutoff - timedelta(days=30)
    start_90 = cutoff - timedelta(days=90)
    within_30 = 0
    within_90 = 0
    tvn_90 = 0

    for row in rows:
        published = _parse_date(row.get("fecha_publicacion", ""))
        if published is None or published > cutoff or published < start_90:
            continue
        within_90 += 1
        if published >= start_30:
            within_30 += 1
        if "tvn" in row.get("medio", "").casefold() or "tvn-2.com" in row.get("url", "").casefold():
            tvn_90 += 1

    return {
        "total": len(rows),
        "within_30_days": within_30,
        "within_90_days": within_90,
        "tvn_within_90_days": tvn_90,
        "minimum_total_within_90_days": 100,
        "minimum_tvn_within_90_days": 20,
    }


def _audit_indicators(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    observed: set[tuple[str, str, int]] = set()
    duplicates: set[tuple[str, str, int]] = set()
    null_values = 0
    invalid_rows = 0

    for row in rows:
        try:
            key = (row["pais_iso3"].strip(), row["indicador_id"].strip(), int(row["anio"]))
        except (KeyError, TypeError, ValueError):
            invalid_rows += 1
            continue
        if key not in EXPECTED_INDICATOR_KEYS:
            invalid_rows += 1
            continue
        if key in observed:
            duplicates.add(key)
        observed.add(key)
        if row.get("valor", "").strip() == "":
            null_values += 1

    return {
        "records": len(rows),
        "expected_combinations": len(EXPECTED_INDICATOR_KEYS),
        "covered_combinations": len(observed),
        "missing_combinations": len(EXPECTED_INDICATOR_KEYS - observed),
        "duplicate_keys": len(duplicates),
        "null_values": null_values,
        "invalid_rows": invalid_rows,
        "pdf_declared_combinations": 1350,
    }


def _audit_usgs(path: Path) -> dict[str, Any]:
    data = _read_json(path) if path.exists() else {}
    features = data.get("features", [])
    invalid = 0
    for feature in features:
        try:
            props = feature["properties"]
            longitude, latitude = feature["geometry"]["coordinates"][:2]
            event_date = datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc).date()
            magnitude = float(props["mag"])
            if not (
                USGS_START <= event_date < USGS_END
                and 5.0 <= float(latitude) <= 12.0
                and -86.0 <= float(longitude) <= -76.0
                and magnitude >= 3.0
            ):
                invalid += 1
        except (KeyError, IndexError, TypeError, ValueError, OSError):
            invalid += 1
    return {
        "records": len(features),
        "invalid_events": invalid,
        "period_utc": f"[{USGS_START.isoformat()}, {USGS_END.isoformat()})",
        "minimum_magnitude": 3.0,
        "bbox": {"min_lat": 5.0, "max_lat": 12.0, "min_lon": -86.0, "max_lon": -76.0},
    }


def _audit_manifest(data_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    items = manifest.get("archivos", [])
    listed = {item.get("archivo"): item.get("sha256") for item in items if isinstance(item, dict)}
    expected_files = ("raw/noticias.csv", "raw/indicadores.csv", "raw/eventos.geojson")
    missing: list[str] = []
    mismatches: list[str] = []
    for relative_path in expected_files:
        file_path = data_dir / relative_path
        expected_hash = listed.get(relative_path)
        if not file_path.is_file() or not expected_hash:
            missing.append(relative_path)
            continue
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            mismatches.append(relative_path)
    return {
        "present": bool(manifest),
        "listed_raw_files": len(listed),
        "missing_files_or_hashes": missing,
        "hash_mismatches": mismatches,
        "valid": bool(manifest) and not missing and not mismatches,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _manifest_cutoff(manifest: dict[str, Any]) -> date:
    return _parse_date(str(manifest.get("fecha_corte_utc", ""))) or datetime.now(timezone.utc).date()


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None
