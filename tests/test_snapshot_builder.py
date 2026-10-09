"""Safety checks for isolated snapshot candidate generation."""

from datetime import date, datetime, timezone
from itertools import product
from pathlib import Path

import pytest

from hackiathon_reto_tvn.adapters.data.live_fetchers import LiveDataFetcher
from hackiathon_reto_tvn.domain.snapshot_contract import (
    SNAPSHOT_COUNTRIES,
    SNAPSHOT_INDICATOR_YEARS,
    SNAPSHOT_INDICATORS,
)
from hackiathon_reto_tvn.services.snapshot_builder import (
    _fetch_gdelt_complete,
    _validate_candidate_path,
    build_candidate_snapshot,
)


def test_snapshot_candidate_must_not_target_active_data(tmp_path: Path) -> None:
    repository_data = Path(__file__).resolve().parents[1] / "data"

    with pytest.raises(ValueError, match="dataset activo congelado"):
        _validate_candidate_path(repository_data)

    with pytest.raises(ValueError, match="dataset activo congelado"):
        _validate_candidate_path(repository_data / "candidates" / "candidate")


def test_snapshot_candidate_accepts_separate_directory(tmp_path: Path) -> None:
    candidate = _validate_candidate_path(tmp_path / "candidate")

    assert candidate == (tmp_path / "candidate").resolve()


@pytest.mark.asyncio
async def test_incomplete_snapshot_is_reported_without_publishing_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_news(*args: object, **kwargs: object) -> list[dict[str, object]]:
        return []

    async def no_indicators(*args: object, **kwargs: object) -> list[dict[str, object]]:
        return []

    monkeypatch.setattr(LiveDataFetcher, "fetch_tvn_rss", no_news)
    monkeypatch.setattr(LiveDataFetcher, "fetch_gdelt", no_news)
    monkeypatch.setattr(LiveDataFetcher, "fetch_world_bank", no_indicators)
    monkeypatch.setattr(LiveDataFetcher, "fetch_usgs", no_news)
    destination = tmp_path / "candidate"

    report = await build_candidate_snapshot(destination)

    assert report["ready"] is False
    assert report["checks"]["indicator_grid"] is True
    assert report["indicators"]["null_values"] == 540
    assert not destination.exists()
    assert (tmp_path / "candidate.audit-report.json").is_file()
    assert list(tmp_path.glob(".*.partial")) == []


@pytest.mark.asyncio
async def test_existing_snapshot_destination_is_never_overwritten(tmp_path: Path) -> None:
    destination = tmp_path / "candidate"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("existing", encoding="utf-8")

    with pytest.raises(ValueError, match="ya existe"):
        await build_candidate_snapshot(destination)

    assert marker.read_text(encoding="utf-8") == "existing"


@pytest.mark.asyncio
async def test_complete_candidate_is_atomically_published(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    today = date.today().isoformat()
    news = [
        {
            "id_noticia": f"N-{index}",
            "titulo": f"Noticia {index}",
            "url": f"https://news.example/{index}",
            "medio": "TVN Noticias" if index < 20 else "Otro medio",
            "fecha_publicacion": today,
            "fecha_deteccion": today,
            "fecha_extraccion": today,
            "idioma": "es",
            "tema": "general",
            "origen": "rss",
            "alcance_texto": "titular_metadatos",
        }
        for index in range(100)
    ]
    indicators = [
        {
            "pais_iso3": country,
            "indicador_id": indicator,
            "anio": year,
            "valor": None,
            "unidad": "%",
            "fuente_url": "https://api.worldbank.org",
            "fecha_extraccion": today,
            "licencia": "CC BY 4.0",
        }
        for country, indicator, year in product(SNAPSHOT_COUNTRIES, SNAPSHOT_INDICATORS, SNAPSHOT_INDICATOR_YEARS)
    ]

    async def news_result(*args: object, **kwargs: object) -> list[dict[str, object]]:
        return news

    async def indicator_result(*args: object, **kwargs: object) -> list[dict[str, object]]:
        return indicators

    async def event_result(*args: object, **kwargs: object) -> list[dict[str, object]]:
        return []

    monkeypatch.setattr(LiveDataFetcher, "fetch_tvn_rss", news_result)
    monkeypatch.setattr(LiveDataFetcher, "fetch_gdelt", news_result)
    monkeypatch.setattr(LiveDataFetcher, "fetch_world_bank", indicator_result)
    monkeypatch.setattr(LiveDataFetcher, "fetch_usgs", event_result)
    destination = tmp_path / "candidate"

    report = await build_candidate_snapshot(destination)

    assert report["ready"] is True
    assert destination.is_dir()
    assert (destination / "audit-report.json").is_file()
    assert (destination / "raw" / "indicadores.csv").is_file()
    assert (destination / "snapshot" / "snapshot.sqlite").is_file()
    assert (destination / "snapshot" / "snapshot_manifest.json").is_file()
    assert not list(tmp_path.glob(".*.partial"))


@pytest.mark.asyncio
async def test_saturated_gdelt_window_is_split_before_accepting_data() -> None:
    class FakeFetcher:
        calls: list[tuple[str, str]] = []

        async def fetch_gdelt(self, **kwargs: object) -> list[dict[str, object]]:
            start = str(kwargs["start_datetime"])
            end = str(kwargs["end_datetime"])
            self.calls.append((start, end))
            if len(self.calls) == 1:
                return [{"url": f"https://news.example/{index}"} for index in range(250)]
            return [{"url": f"https://news.example/split-{len(self.calls)}"}]

    fetcher = FakeFetcher()
    results = await _fetch_gdelt_complete(
        fetcher, datetime(2026, 7, 1, tzinfo=timezone.utc), datetime(2026, 9, 29, tzinfo=timezone.utc)
    )

    assert len(fetcher.calls) == 3
    assert len(results) == 2
    assert fetcher.calls[1][1] >= fetcher.calls[2][0]
