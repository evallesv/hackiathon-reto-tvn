"""Unit tests for data loaders, manifest generation, and deduplication."""

import json
import shutil
from pathlib import Path

from hackiathon_reto_tvn.adapters.data.loaders import (
    EventGrouper,
    LocalStorageRepository,
)
from hackiathon_reto_tvn.domain.models import Noticia


def test_load_noticias() -> None:
    repo = LocalStorageRepository()
    noticias = repo.load_noticias(Path("data/raw/noticias.csv"))
    assert len(noticias) >= 10
    tvn_count = sum(1 for n in noticias if "tvn" in n.medio.lower())
    assert tvn_count >= 1


def test_load_indicadores_null_preservation() -> None:
    repo = LocalStorageRepository()
    indicadores = repo.load_indicadores(Path("data/raw/indicadores.csv"))
    assert len(indicadores) > 0
    # Al menos un indicador debe conservar un valor nulo de manera explícita (T01)
    null_entries = [i for i in indicadores if i.valor is None]
    assert len(null_entries) >= 1


def test_load_eventos_geojson() -> None:
    repo = LocalStorageRepository()
    eventos = repo.load_eventos(Path("data/raw/eventos.geojson"))
    assert len(eventos) == 3
    assert eventos[0].magnitude >= 3.0


def test_manifest_sha256_generation(tmp_path: Path) -> None:
    # Never regenerate in place: data/manifest.json is a frozen snapshot.
    frozen = Path("data/manifest.json")
    before = frozen.read_bytes()
    data_copy = tmp_path / "data"
    shutil.copytree("data", data_copy)

    manifest = LocalStorageRepository().generate_manifest(data_copy)

    assert manifest.version == "v1.0"
    assert len(manifest.archivos) == 3
    for item in manifest.archivos:
        assert len(item.sha256) == 64  # Valid SHA-256 hex string
    written = json.loads((data_copy / "manifest.json").read_text(encoding="utf-8"))
    assert "fecha_corte_utc" in written
    assert "fecha_corte_UTC" not in written
    assert frozen.read_bytes() == before


def test_event_grouper_deduplication() -> None:
    n1 = Noticia(
        id_noticia="N1",
        titulo="MOP anuncia plan vial en Panamá",
        url="https://tvn.com/1",
        medio="TVN",
        fecha_publicacion="2024-03-10",
        fecha_deteccion="2024-03-10",
        fecha_extraccion="2024-03-10",
        tema="servicios",
        origen="rss",
    )
    n2 = Noticia(
        id_noticia="N2",
        titulo="MOP anuncia plan vial urgente",
        url="https://critica.com/2",
        medio="Critica",
        fecha_publicacion="2024-03-10",
        fecha_deteccion="2024-03-10",
        fecha_extraccion="2024-03-10",
        tema="servicios",
        origen="gdelt",
    )
    clusters = EventGrouper.group_articles([n1, n2])
    # Ambas noticias comparten los primeros 3 tokens significativos ('anuncia', 'plan', 'vial')
    # por lo que deben agruparse bajo el mismo cluster
    assert len(clusters) == 1
    grouped_items = list(clusters.values())[0]
    assert len(grouped_items) == 2
