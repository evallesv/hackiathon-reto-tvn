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


def test_load_indicadores_preserves_missing_country_and_year_as_null(tmp_path: Path) -> None:
    path = tmp_path / "indicadores.csv"
    path.write_text("pais_iso3,indicador_id,anio,valor,unidad\n,NY.GDP.MKTP.CD,,12.5,USD\n", encoding="utf-8")

    indicadores = LocalStorageRepository().load_indicadores(path)

    assert len(indicadores) == 1
    assert indicadores[0].pais_iso3 is None
    assert indicadores[0].indicador_id == "NY.GDP.MKTP.CD"
    assert indicadores[0].anio is None


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


def test_event_grouper_matches_paraphrased_headlines_with_shared_entities() -> None:
    first = Noticia(
        id_noticia="N1",
        titulo="Canal de Panamá reduce tránsito por sequía",
        url="https://tvn.com/1",
        medio="TVN",
        fecha_publicacion="2026-10-01",
        fecha_deteccion="2026-10-01",
        fecha_extraccion="2026-10-01",
        tema="logistica",
        origen="rss",
    )
    paraphrase = Noticia(
        id_noticia="N2",
        titulo="Sequía obliga al Canal de Panamá a limitar el tránsito",
        url="https://critica.com/2",
        medio="Critica",
        fecha_publicacion="2026-10-02",
        fecha_deteccion="2026-10-02",
        fecha_extraccion="2026-10-02",
        tema="logistica",
        origen="rss",
    )

    clusters = EventGrouper.group_articles([first, paraphrase])

    assert len(clusters) == 1
    assert len(next(iter(clusters.values()))) == 2


def test_event_grouper_does_not_merge_different_events_with_generic_opening() -> None:
    first = Noticia(
        id_noticia="N1",
        titulo="Gobierno anuncia plan de seguridad nacional",
        url="https://tvn.com/1",
        medio="TVN",
        fecha_publicacion="2026-10-01",
        fecha_deteccion="2026-10-01",
        fecha_extraccion="2026-10-01",
        tema="politica",
        origen="rss",
    )
    second = first.model_copy(
        update={
            "id_noticia": "N2",
            "titulo": "Gobierno anuncia plan de vacunación escolar",
            "url": "https://critica.com/2",
            "medio": "Critica",
        }
    )

    clusters = EventGrouper.group_articles([first, second])

    assert len(clusters) == 2
