#!/usr/bin/env python3
"""Build a read-only SQLite snapshot package from the frozen raw data and manifest."""

import argparse
import json
from pathlib import Path

from hackiathon_reto_tvn.adapters.data.sqlite_snapshot import SQLiteSnapshotRepository
from hackiathon_reto_tvn.config import get_settings


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=settings.DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=settings.SQLITE_SNAPSHOT_PATH.parent)
    args = parser.parse_args()

    operational_db = settings.SQLITE_DB_PATH if settings.SQLITE_DB_PATH.is_file() else None
    snapshot = SQLiteSnapshotRepository.create_from_directory(
        args.data_dir,
        args.output_dir,
        operational_db_path=operational_db,
        live_window_days=settings.LIVE_AGENDA_MAX_AGE_DAYS,
    )
    manifest = json.loads((args.output_dir / "snapshot_manifest.json").read_text(encoding="utf-8"))
    print(f"Snapshot SQLite creado: {snapshot.database_path}")
    print(f"Registros incluidos: {manifest['counts']}")
    print(f"SHA-256: {manifest['snapshot_sha256']}")
    print("Tablas de revisión e ingesta operativa excluidas.")


if __name__ == "__main__":
    main()
