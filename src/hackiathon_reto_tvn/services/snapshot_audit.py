"""Read-only compliance audit for proposed HackIAthon public-data snapshots."""

import csv
import hashlib
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hackiathon_reto_tvn.domain.snapshot_contract import EXPECTED_INDICATOR_KEYS

USGS_START = date(2024, 1, 1)
USGS_END = date(2025, 1, 1)


def audit_snapshot(data_dir: Path) -> dict[str, Any]:
    """Check the challenge minimums without writing to the candidate snapshot."""
    manifest_path = data_dir / "manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    manifest_audit = _audit_manifest(data_dir, manifest)
    sqlite_audit = _audit_sqlite_snapshot(data_dir, manifest_audit)
    snapshot_manifest = _read_json(data_dir / "snapshot" / "snapshot_manifest.json")
    snapshot_rows = _read_sqlite_snapshot_records(data_dir) if sqlite_audit["valid"] else None
    if snapshot_rows is None:
        cutoff_date = _manifest_cutoff(manifest)
        news = _audit_news(data_dir / "raw" / "noticias.csv", cutoff_date)
        indicators = _audit_indicators(data_dir / "raw" / "indicadores.csv")
        usgs = _audit_usgs(data_dir / "raw" / "eventos.geojson")
        dataset_source = "raw_fallback"
    else:
        cutoff_date = _manifest_cutoff(snapshot_manifest)
        news = _audit_news_rows(snapshot_rows["noticias"], cutoff_date)
        indicators = _audit_indicator_rows(snapshot_rows["indicadores"])
        usgs = _audit_usgs_rows(snapshot_rows["eventos"])
        dataset_source = "sqlite_snapshot"

    checks = {
        "news_minimum": news["within_90_days"] >= 100 and news["tvn_within_90_days"] >= 20,
        "indicator_grid": (
            indicators["covered_combinations"] == 540
            and indicators["duplicate_keys"] == 0
            and indicators["invalid_rows"] == 0
        ),
        "usgs_scope": usgs["invalid_events"] == 0,
        "manifest_hashes": manifest_audit["valid"],
        "sqlite_snapshot": sqlite_audit["valid"],
    }
    return {
        "data_dir": str(data_dir),
        "dataset_source": dataset_source,
        "cutoff_date": cutoff_date.isoformat(),
        "ready": all(checks.values()),
        "checks": checks,
        "news": news,
        "indicators": indicators,
        "usgs": usgs,
        "manifest": manifest_audit,
        "sqlite_snapshot": sqlite_audit,
        "notes": [
            "La cuadrícula del PDF tiene 6 países x 6 indicadores x 15 años = 540 combinaciones; el valor 1,350 indicado allí no coincide con esos ejes.",
            "Esta auditoría comprueba estructura y alcance, no licencias por registro, calidad editorial ni pertinencia semántica.",
            "Los eventos vivos están separados y no se cuentan como parte del catálogo USGS 2024 requerido.",
        ],
    }


def _audit_news(path: Path, cutoff: date) -> dict[str, Any]:
    return _audit_news_rows(_read_csv(path), cutoff)


def _audit_news_rows(rows: list[dict[str, Any]], cutoff: date) -> dict[str, Any]:
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
    return _audit_indicator_rows(_read_csv(path))


def _audit_indicator_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
        if row.get("valor") is None or str(row.get("valor", "")).strip() == "":
            null_values += 1

    return {
        "records": len(rows),
        "expected_combinations": len(EXPECTED_INDICATOR_KEYS),
        "covered_combinations": len(observed),
        "missing_combinations": len(EXPECTED_INDICATOR_KEYS - observed),
        "duplicate_keys": len(duplicates),
        "null_values": null_values,
        "populated_values": len(rows) - null_values,
        "indicators_with_values": len(
            {
                row.get("indicador_id")
                for row in rows
                if row.get("valor") is not None and str(row.get("valor", "")).strip() != ""
            }
        ),
        "invalid_rows": invalid_rows,
        "pdf_declared_combinations": 1350,
    }


def _audit_usgs(path: Path) -> dict[str, Any]:
    data = _read_json(path) if path.exists() else {}
    return _audit_usgs_features(data.get("features", []))


def _audit_usgs_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    features = [
        {
            "properties": {"time": row["time"], "mag": row["magnitude"]},
            "geometry": {"coordinates": [row["longitude"], row["latitude"], row["depth"]]},
        }
        for row in rows
    ]
    return _audit_usgs_features(features)


def _audit_usgs_features(features: list[dict[str, Any]]) -> dict[str, Any]:
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
        "source_manifest_sha256": hashlib.sha256((data_dir / "manifest.json").read_bytes()).hexdigest()
        if (data_dir / "manifest.json").is_file()
        else None,
        "listed_raw_files": len(listed),
        "missing_files_or_hashes": missing,
        "hash_mismatches": mismatches,
        "valid": bool(manifest) and not missing and not mismatches,
    }


def _audit_sqlite_snapshot(data_dir: Path, manifest_audit: dict[str, Any]) -> dict[str, Any]:
    database_path = data_dir / "snapshot" / "snapshot.sqlite"
    package_manifest_path = data_dir / "snapshot" / "snapshot_manifest.json"
    if not database_path.is_file() or not package_manifest_path.is_file():
        return {"valid": False, "reason": "Falta snapshot/snapshot.sqlite o snapshot_manifest.json"}

    try:
        package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
        database_hash = hashlib.sha256(database_path.read_bytes()).hexdigest()
        with sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {
                row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            counts = {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("noticias", "indicadores", "eventos", "eventos_vivos")
                if table in tables
            }
        expected_counts = package_manifest.get("counts", {})
        required_tables = {"snapshot_metadata", "noticias", "indicadores", "eventos", "eventos_vivos"}
        valid = (
            integrity == "ok"
            and required_tables.issubset(tables)
            and "fichas_casos" not in tables
            and "ingestion_runs" not in tables
            and database_hash == package_manifest.get("snapshot_sha256")
            and package_manifest.get("source_manifest_sha256") == manifest_audit.get("source_manifest_sha256")
            and counts == expected_counts
        )
        return {
            "valid": valid,
            "integrity_check": integrity,
            "tables": sorted(tables),
            "counts": counts,
            "hash_matches": database_hash == package_manifest.get("snapshot_sha256"),
            "source_manifest_matches": package_manifest.get("source_manifest_sha256")
            == manifest_audit.get("source_manifest_sha256"),
        }
    except (OSError, sqlite3.Error, KeyError, TypeError, ValueError):
        return {"valid": False, "reason": "No se pudo validar el paquete SQLite"}


def _read_sqlite_snapshot_records(data_dir: Path) -> dict[str, list[dict[str, Any]]] | None:
    database_path = data_dir / "snapshot" / "snapshot.sqlite"
    try:
        with sqlite3.connect(f"{database_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            return {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table}").fetchall()]
                for table in ("noticias", "indicadores", "eventos")
            }
    except (OSError, sqlite3.Error):
        return None


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
