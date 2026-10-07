"""Tests for live data fetchers (offline with mocks per T10)."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from hackiathon_reto_tvn.adapters.data.live_fetchers import (
    LiveDataFetcher,
    _generate_article_id,
    _parse_rfc822_or_iso,
)
from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage


def test_date_parsing_and_id_generation() -> None:
    # RFC 822
    rfc = "Tue, 06 Oct 2026 23:57:05 +0000"
    iso = _parse_rfc822_or_iso(rfc)
    assert "2026-10-06" in iso

    # ISO format
    iso_input = "2026-10-06T12:00:00Z"
    iso_output = _parse_rfc822_or_iso(iso_input)
    assert "2026-10-06" in iso_output

    # Fallback on empty or invalid
    fallback = _parse_rfc822_or_iso(None)
    assert len(fallback) > 10

    # ID generation
    url = "https://www.tvn-2.com/nacionales/noticia-1.html"
    art_id = _generate_article_id(url)
    assert art_id.startswith("NOT-LIVE-")
    assert art_id == _generate_article_id(url)  # deterministic


@pytest.mark.asyncio
async def test_live_fetcher_sync_all_mocked(tmp_path: Path) -> None:
    storage = SQLiteStorage(tmp_path / "sync_test.db")
    fetcher = LiveDataFetcher()

    mock_rss_items = [
        {
            "id_noticia": "NOT-LIVE-01",
            "titulo": "Noticia TVN en vivo",
            "url": "https://www.tvn-2.com/nacionales/test1.html",
            "medio": "TVN Noticias",
            "fecha_publicacion": "2026-10-06T12:00:00Z",
        }
    ]

    mock_gdelt_items = [
        {
            "id_noticia": "NOT-LIVE-02",
            "titulo": "Noticia GDELT en vivo",
            "url": "https://example.com/gdelt1.html",
            "medio": "La Estrella",
            "fecha_publicacion": "2026-10-06T12:00:00Z",
        }
    ]

    mock_wb_items = [
        {
            "pais_iso3": "PAN",
            "indicador_id": "NY.GDP.MKTP.KD.ZG",
            "anio": 2023,
            "valor": 7.3,
            "unidad": "%",
            "fuente_url": "https://api.worldbank.org",
        }
    ]

    mock_usgs_items = [
        {
            "id": "us7000test",
            "magnitude": 4.2,
            "place": "Golfo de Chiriquí",
            "time": 1710386100000,
            "latitud": 7.42,
            "longitud": -82.85,
        }
    ]

    with (
        patch.object(fetcher, "fetch_tvn_rss", new_callable=AsyncMock, return_value=mock_rss_items),
        patch.object(fetcher, "fetch_gdelt", new_callable=AsyncMock, return_value=mock_gdelt_items),
        patch.object(fetcher, "fetch_world_bank", new_callable=AsyncMock, return_value=mock_wb_items),
        patch.object(fetcher, "fetch_usgs", new_callable=AsyncMock, return_value=mock_usgs_items),
    ):
        result = await fetcher.sync_all(storage)

        assert result["sources"]["tvn_rss"]["status"] == "SUCCESS"
        assert result["sources"]["tvn_rss"]["count"] == 1
        assert result["sources"]["gdelt"]["status"] == "SUCCESS"
        assert result["sources"]["gdelt"]["count"] == 1
        assert result["sources"]["world_bank"]["status"] == "SUCCESS"
        assert result["sources"]["world_bank"]["count"] == 1
        assert result["sources"]["usgs"]["status"] == "SUCCESS"
        assert result["sources"]["usgs"]["count"] == 1

        db_stats = result["db_stats"]
        assert db_stats["total_noticias"] == 2
        assert db_stats["total_indicadores"] == 1
        assert db_stats["total_eventos"] == 1
        assert db_stats["total_runs"] == 4
