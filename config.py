# Configuración del script scripts/ingesta_datasets.py (CKAN datosabiertos.gob.pa).
# La base SQLite NO se configura aquí: se usa SQLITE_DB_PATH del app (hackiathon_reto_tvn.config).

BASE_URL = "https://www.datosabiertos.gob.pa/api/action"

YEAR = 2026

MONTHS = {
    8: "agosto",
    9: "septiembre",
    10: "octubre",
}

TOTAL_RECORDS_PER_DATASET = 99

MONTHS_COUNT = len(MONTHS)

RECORDS_PER_MONTH = TOTAL_RECORDS_PER_DATASET // MONTHS_COUNT

REQUEST_TIMEOUT = 30

# Categorías (grupos CKAN). Tres slugs reales difieren del nombre visible:
# gobiernos-locales -> municipios, finanzas-de-gobierno -> gobierno-finanzas, desarrollo-social -> social-desarrollo
CATEGORIES = [
    "orden-publico-y-seguridad",
    "justicia",
    "salud",
    "estadisticas-de-gobierno",
    "ambiente",
    "municipios",
    "transporte-y-logistica",
    "gobierno-finanzas",
    "social-desarrollo",
]

# Datasets sensibles que no se ingestan: se excluyen si su nombre o título contiene alguna de estas palabras
# (se comparan en minúsculas y sin tildes). onpar = Oficina Nacional para la Atención de Refugiados;
# iei = Instituto de Estudios Interdisciplinarios (menores en conflicto con la ley).
EXCLUDE_KEYWORDS = [
    "refugiad",
    "onpar",
    "conare",
    "mingob-iei",
    "conflictos-con-la-ley",
    "conflicto con la ley",
    "menores",
    "adolescente",
    "ninez",
    "niñez",
    "penitenciari",
    "mandamientos",
    "boletas-de-libertad",
]

# Además se excluyen los datasets cuyo nombre (slug) menciona un año distinto de YEAR sin mencionar YEAR.

PACKAGE_SEARCH_ROWS = 100

# Pausa entre requests (segundos) para no saturar el portal.
REQUEST_DELAY = 0.2

# Slugs (package id) adicionales a consumir de forma explícita, además de las categorías.
DATASETS: list[str] = []
