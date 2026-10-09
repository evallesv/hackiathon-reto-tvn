#!/usr/bin/env python3
"""Audit a candidate data snapshot without changing source files."""

import argparse
import json
import sys
from pathlib import Path

from hackiathon_reto_tvn.services.snapshot_audit import audit_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita una carpeta candidata de snapshot sin modificarla")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Carpeta con raw/ y manifest.json")
    args = parser.parse_args()

    report = audit_snapshot(args.data_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
