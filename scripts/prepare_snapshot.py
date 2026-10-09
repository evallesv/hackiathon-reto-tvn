#!/usr/bin/env python3
"""Prepare an isolated live-data snapshot candidate and report challenge coverage."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from hackiathon_reto_tvn.services.snapshot_builder import build_candidate_snapshot


async def _run(output_dir: Path) -> int:
    report = await build_candidate_snapshot(output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara un snapshot candidato aislado para auditarlo")
    parser.add_argument("--output-dir", type=Path, required=True, help="Destino fuera de data/ activo")
    args = parser.parse_args()
    try:
        return asyncio.run(_run(args.output_dir))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"No se pudo preparar el snapshot candidato: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
