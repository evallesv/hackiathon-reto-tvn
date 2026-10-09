"""Tests for live data fetchers (offline with mocks per T10)."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from hackiathon_reto_tvn.adapters.data.live_fetchers import (
    LiveDataFetcher,
    _generate_article_id,
    _parse_rfc822_or_iso,
)
from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage


@pytest.mark.asyncio
async def test_gdelt_seendate_is_detection_time_not_publication_time(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    class Response:
        status_code = 200
        headers = {"content-type": "application/json"}
        text = '{"articles": [{"url": "https://example.com/article", "title": "Titular", "seendate": "20240311T104500Z", "domain": "example.com"}]}'

        def json(self) -> dict[str, list[dict[str, str]]]:
            return {
                "articles": [
                    {
                        "url": "https://example.com/article",
                        "title": "Titular",
                        "seendate": "20240311T104500Z",
                        "domain": "example.com",
                    }
                ]
            }

    class AsyncClient:
        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> Response:
            requested_urls.append(url)
            return Response()

    monkeypatch.setattr(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.httpx.AsyncClient", lambda **kwargs: AsyncClient()
    )

    [article] = await LiveDataFetcher().fetch_gdelt(start_datetime="20260801000000", end_datetime="20261001000000")

    assert article["fecha_publicacion"] == ""
    assert article["fecha_deteccion"].startswith("2024-03-11T10:45:00")
    assert "startdatetime=20260801000000" in requested_urls[0]
    assert "enddatetime=20261001000000" in requested_urls[0]


@pytest.mark.asyncio
async def test_world_bank_fetch_accepts_full_challenge_year_range(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    class Response:
        status_code = 200

        def json(self) -> list[object]:
            return [{}, [{"date": "2010", "value": None}]]

    class AsyncClient:
        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> Response:
            requested_urls.append(url)
            return Response()

    monkeypatch.setattr(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.httpx.AsyncClient", lambda **kwargs: AsyncClient()
    )

    records = await LiveDataFetcher().fetch_world_bank(
        countries=["PAN"], indicators=["NY.GDP.MKTP.KD.ZG"], start_year=2010, end_year=2024
    )

    assert len(records) == 1
    assert records[0]["anio"] == 2010
    assert records[0]["valor"] is None
    assert "date=2010:2024" in requested_urls[0]


@pytest.mark.asyncio
async def test_world_bank_fetch_keeps_successful_indicators_when_one_request_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        status_code = 200

        def json(self) -> list[object]:
            return [{}, [{"date": "2024", "value": 2.5}]]

    class AsyncClient:
        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> Response:
            if "CRI/indicator/FP.CPI" in url:
                raise OSError("simulated timeout")
            return Response()

    monkeypatch.setattr(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.httpx.AsyncClient", lambda **kwargs: AsyncClient()
    )

    records = await LiveDataFetcher().fetch_world_bank(
        countries=["PAN", "CRI"],
        indicators=["NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG"],
        start_year=2024,
        end_year=2024,
    )

    assert len(records) == 3
    assert all(row["anio"] == 2024 for row in records)


@pytest.mark.asyncio
async def test_world_bank_fetch_runs_multiple_requests_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    active_requests = 0
    peak_requests = 0

    class Response:
        status_code = 200

        def json(self) -> list[object]:
            return [{}, []]

    class AsyncClient:
        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> Response:
            nonlocal active_requests, peak_requests
            active_requests += 1
            peak_requests = max(peak_requests, active_requests)
            await asyncio.sleep(0)
            active_requests -= 1
            return Response()

    monkeypatch.setattr(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.httpx.AsyncClient", lambda **kwargs: AsyncClient()
    )

    await LiveDataFetcher().fetch_world_bank(
        countries=["PAN", "CRI", "COL"], indicators=["GDP", "CPI"], start_year=2024, end_year=2024
    )

    assert 1 < peak_requests <= 6


@pytest.mark.asyncio
async def test_usgs_fetch_accepts_challenge_period(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    class Response:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, list[object]]:
            return {"features": []}

    class AsyncClient:
        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get(self, url: str) -> Response:
            requested_urls.append(url)
            return Response()

    monkeypatch.setattr(
        "hackiathon_reto_tvn.adapters.data.live_fetchers.httpx.AsyncClient", lambda **kwargs: AsyncClient()
    )

    await LiveDataFetcher().fetch_usgs(start_time="2024-01-01", end_time="2025-01-01")

    assert "starttime=2024-01-01" in requested_urls[0]
    assert "endtime=2025-01-01" in requested_urls[0]


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
