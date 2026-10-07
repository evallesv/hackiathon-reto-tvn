#!/usr/bin/env python3
"""Standalone script to execute periodic live data ingestion into SQLite.

Usage:
    # Single execution:
    uv run python scripts/periodic_ingestion.py

    # Continuous loop execution (e.g. background worker):
    uv run python scripts/periodic_ingestion.py --continuous --interval 60
"""

import argparse
import asyncio
import logging
import sys

from hackiathon_reto_tvn.config import get_settings
from hackiathon_reto_tvn.services.ingestion_scheduler import run_ingestion_cycle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("periodic_ingestion")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta periódica de datos de fuentes reales")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Ejecutar en bucle continuo a intervalos regulares",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Intervalo en minutos para el modo continuo (default: 60)",
    )
    args = parser.parse_args()

    settings = get_settings()
    logger.info(f"Ruta de base de datos SQLite: {settings.SQLITE_DB_PATH}")

    if not args.continuous:
        logger.info("Ejecutando ciclo de ingesta único...")
        report = await run_ingestion_cycle(settings)
        logger.info(f"Ciclo completado: {report.get('sources')}")
        logger.info(f"Estadísticas BD: {report.get('db_stats')}")
        sys.exit(0)

    interval_secs = max(60, args.interval * 60)
    logger.info(f"Iniciando modo continuo cada {args.interval} minutos ({interval_secs}s)...")
    while True:
        try:
            report = await run_ingestion_cycle(settings)
            logger.info(f"Ciclo completado: {report.get('sources')}")
        except Exception as exc:
            logger.error(f"Error en ciclo de ingesta: {exc}", exc_info=True)

        logger.info(f"Esperando {args.interval} minutos para el siguiente ciclo...")
        await asyncio.sleep(interval_secs)


if __name__ == "__main__":
    asyncio.run(main())
