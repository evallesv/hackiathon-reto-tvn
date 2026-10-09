"""Tests for read-only readiness checks on proposed public-data snapshots."""

import csv
from datetime import date, timedelta
from itertools import product
from pathlib import Path

from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository
from hackiathon_reto_tvn.services.snapshot_audit import audit_snapshot


def test_snapshot_audit_reports_coverage_gaps_without_mutating_input(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    news_path = raw_dir / "noticias.csv"
    with news_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["id_noticia", "titulo", "url", "medio", "fecha_publicacion"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "id_noticia": "NOT-001",
                "titulo": "Titular de TVN",
                "url": "https://tvn-2.com/noticia",
                "medio": "TVN Noticias",
                "fecha_publicacion": "2026-10-01T12:00:00Z",
            }
        )
    (raw_dir / "indicadores.csv").write_text("pais_iso3,indicador_id,anio,valor\nPAN,x,2020,\n", encoding="utf-8")
    (raw_dir / "eventos.geojson").write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        '{"fecha_corte_utc":"2026-10-08T00:00:00Z","archivos":[]}', encoding="utf-8"
    )
    before = {path.name: path.read_bytes() for path in raw_dir.iterdir()}

    report = audit_snapshot(tmp_path)

    assert report["ready"] is False
    assert report["news"]["within_90_days"] == 1
    assert report["news"]["tvn_within_90_days"] == 1
    assert report["indicators"]["expected_combinations"] == 540
    assert report["indicators"]["covered_combinations"] == 0
    assert {path.name: path.read_bytes() for path in raw_dir.iterdir()} == before


def test_snapshot_audit_counts_null_indicator_rows_as_covered(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "noticias.csv").write_text("id_noticia,titulo,url,medio,fecha_publicacion\n", encoding="utf-8")
    (raw_dir / "indicadores.csv").write_text(
        "pais_iso3,indicador_id,anio,valor\nPAN,NY.GDP.MKTP.KD.ZG,2010,\n", encoding="utf-8"
    )
    (raw_dir / "eventos.geojson").write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    (tmp_path / "manifest.json").write_text('{"archivos":[]}', encoding="utf-8")

    report = audit_snapshot(tmp_path)

    assert report["indicators"]["covered_combinations"] == 1
    assert report["indicators"]["null_values"] == 1


def test_complete_candidate_snapshot_passes_the_structural_gate(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    news_path = raw_dir / "noticias.csv"
    cutoff = date.today()
    with news_path.open("w", encoding="utf-8", newline="") as stream:
        fields = ["id_noticia", "titulo", "url", "medio", "fecha_publicacion"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index in range(100):
            writer.writerow(
                {
                    "id_noticia": f"NOT-{index:03d}",
                    "titulo": f"Titular público {index}",
                    "url": f"https://tvn-2.com/noticia/{index}",
                    "medio": "TVN Noticias" if index < 20 else "Medio público",
                    "fecha_publicacion": (cutoff - timedelta(days=1)).isoformat(),
                }
            )

    indicators_path = raw_dir / "indicadores.csv"
    with indicators_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["pais_iso3", "indicador_id", "anio", "valor"])
        writer.writeheader()
        for country, indicator, year in product(
            ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"],
            [
                "NY.GDP.MKTP.KD.ZG",
                "FP.CPI.TOTL.ZG",
                "SL.UEM.TOTL.ZS",
                "SP.POP.TOTL",
                "IT.NET.USER.ZS",
                "NE.EXP.GNFS.ZS",
            ],
            range(2010, 2025),
        ):
            writer.writerow({"pais_iso3": country, "indicador_id": indicator, "anio": year, "valor": ""})
    (raw_dir / "eventos.geojson").write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    LocalStorageRepository().generate_manifest(tmp_path)

    report = audit_snapshot(tmp_path)

    assert report["ready"] is True
    assert all(report["checks"].values())
