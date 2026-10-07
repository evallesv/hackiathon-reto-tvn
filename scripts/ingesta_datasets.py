"""Ingesta de datos abiertos (CKAN datosabiertos.gob.pa) como fuente de contraste de las noticias.

Por cada categoría de CATEGORIES elige UN dataset y guarda sus registros en la tabla `datasets_live` de la SQLite
del app (SQLITE_DB_PATH), igual que sismos (USGS) e indicadores (Banco Mundial). Cada dataset queda registrado en
`ingestion_runs`.

Este script NO crea la base ni las tablas: eso lo hace el app al iniciar (`SQLiteStorage.init_db`).

Selección por categoría:
  1. package_search filtrado por grupo y ordenado por metadata_modified desc (el filtro lo hace la API).
  2. Primer dataset no excluido (EXCLUDE_KEYWORDS) con al menos un recurso CSV consultable (datastore activo)
     cuyo nombre menciona YEAR y ningún otro año.
  3. Hasta TOTAL_RECORDS_PER_DATASET registros (datastore_search), de sus recursos más nuevos a más viejos.

Uso:
    uv run python scripts/ingesta_datasets.py            # elige + ingesta
    uv run python scripts/ingesta_datasets.py --discover # solo muestra qué dataset elegiría por categoría
"""

import importlib
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.config import get_settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
cfg = importlib.import_module("config")

BASE_URL: str = cfg.BASE_URL
CATEGORIES: list[str] = cfg.CATEGORIES
EXCLUDE_KEYWORDS: list[str] = cfg.EXCLUDE_KEYWORDS
REQUEST_DELAY: float = cfg.REQUEST_DELAY
REQUEST_TIMEOUT: int = cfg.REQUEST_TIMEOUT
TOTAL_RECORDS_PER_DATASET: int = cfg.TOTAL_RECORDS_PER_DATASET
YEAR: int = cfg.YEAR
CANDIDATES_PER_CATEGORY = 50  # cuántos datasets recientes de la categoría se evalúan hasta hallar uno válido

MONTH_NAMES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def is_excluded(package: dict[str, Any]) -> bool:
    """Excluye datasets sensibles (EXCLUDE_KEYWORDS) y los que por su nombre son de otro año distinto de YEAR."""
    text = _normalize(f"{package.get('name', '')} {package.get('title', '')}")
    if any(_normalize(keyword) in text for keyword in EXCLUDE_KEYWORDS):
        return True
    years = set(re.findall(r"(?<!\d)20\d\d(?!\d)", package.get("name", "")))
    return bool(years) and str(YEAR) not in years


def api_get(client: httpx.Client, endpoint: str, params: dict[str, Any]) -> Any:
    response = client.get(f"{BASE_URL}/{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"CKAN API error: {data}")
    time.sleep(REQUEST_DELAY)
    return data["result"]


def is_year_resource(resource: dict[str, Any]) -> bool:
    """El nombre del recurso menciona YEAR y ningún otro año (descarta 'Fisioterapia-2025' y rangos '2019 al 2026')."""
    years = set(re.findall(r"(?<!\d)20\d\d(?!\d)", resource.get("name") or ""))
    return years == {str(YEAR)}


def csv_resources(package: dict[str, Any]) -> list[dict[str, Any]]:
    """Recursos CSV consultables (datastore activo) de YEAR, del más nuevo al más viejo."""
    found = [
        r
        for r in package.get("resources", [])
        if (r.get("format") or "").upper() == "CSV" and r.get("datastore_active") and is_year_resource(r)
    ]
    return sorted(found, key=lambda r: r.get("last_modified") or r.get("created") or "", reverse=True)


def pick_dataset(client: httpx.Client, category: str, already_taken: set[str]) -> dict[str, Any] | None:
    """Dataset más recientemente modificado de la categoría, no excluido, con CSV consultable y no elegido antes."""
    result = api_get(
        client,
        "package_search",
        {"fq": f"groups:{category}", "sort": "metadata_modified desc", "rows": CANDIDATES_PER_CATEGORY},
    )
    for package in result.get("results", []):
        if package["name"] not in already_taken and not is_excluded(package) and csv_resources(package):
            return package  # type: ignore[no-any-return]
    return None


def resource_month(resource: dict[str, Any]) -> int:
    """Mes deducido del nombre del recurso; 0 si no se menciona."""
    name = _normalize(resource.get("name") or "")
    return next((number for word, number in MONTH_NAMES.items() if word in name), 0)


def ingest_dataset(client: httpx.Client, category: str, package: dict[str, Any]) -> list[dict[str, Any]]:
    """Hasta TOTAL_RECORDS_PER_DATASET registros listos para `replace_dataset_records`."""
    records: list[dict[str, Any]] = []
    organizacion = (package.get("organization") or {}).get("title") or ""
    for resource in csv_resources(package):
        remaining = TOTAL_RECORDS_PER_DATASET - len(records)
        if remaining <= 0:
            break
        result = api_get(client, "datastore_search", {"resource_id": resource["id"], "limit": remaining})
        rows = result.get("records", [])
        print(f"    + {len(rows)} de '{(resource.get('name') or '').strip()}' (disponibles: {result.get('total')})")
        for index, row in enumerate(rows):
            records.append(
                {
                    "categoria": category,
                    "titulo_dataset": package.get("title") or "",
                    "organizacion": organizacion,
                    "anio": YEAR,
                    "mes": resource_month(resource),
                    "resource_id": resource["id"],
                    "record_id": row.get("_id", index),
                    "payload": row,
                }
            )
    return records


def main() -> None:
    discover_only = "--discover" in sys.argv
    storage = SQLiteStorage(get_settings().SQLITE_DB_PATH)
    if not discover_only and not storage.has_table("datasets_live"):
        sys.exit(
            f"La tabla datasets_live no existe en {storage.db_path}. "
            "Inicia el app (o SQLiteStorage.init_db) para crear el esquema y vuelve a ejecutar."
        )

    selected: list[str] = []
    with httpx.Client() as client:
        for category in CATEGORIES:
            started = datetime.now(timezone.utc).isoformat()
            try:
                package = pick_dataset(client, category, set(selected))
            except Exception as exc:
                print(f"{category}: ERROR {exc}")
                continue
            if package is None:
                print(f"{category}: sin dataset elegible (ninguno con CSV consultable de {YEAR})")
                continue
            name = package["name"]
            print(f"{category}: {name} (modificado {package['metadata_modified'][:10]})")
            selected.append(name)
            if discover_only:
                continue
            try:
                records = ingest_dataset(client, category, package)
                count = storage.replace_dataset_records(name, records)
                detalles = f"Ingested {count} records for category {category}"
                storage.record_run(
                    f"datos_abiertos:{name}",
                    "SUCCESS",
                    count,
                    detalles,
                    started,
                    datetime.now(timezone.utc).isoformat(),
                )
                print(f"  Guardados {count} registros")
            except Exception as exc:
                storage.record_run(
                    f"datos_abiertos:{name}", "ERROR", 0, str(exc), started, datetime.now(timezone.utc).isoformat()
                )
                print(f"  ERROR en {name}: {exc}")

    if not discover_only and selected:
        # La tabla refleja exactamente la selección actual: se eliminan datasets de corridas anteriores.
        print(f"\nFilas eliminadas de datasets que ya no están en la selección: {storage.prune_datasets(selected)}")
    if not discover_only:
        print(f"Totales en {storage.db_path}: {storage.get_stats()['total_datasets']} filas en datasets_live")


if __name__ == "__main__":
    main()
