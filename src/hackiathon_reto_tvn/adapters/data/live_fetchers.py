"""Live Data Fetchers for TVN RSS, GDELT, World Bank, and USGS APIs.

Provides real-time ingestion from the official sources specified in the hackathon challenge:
1. TVN Noticias RSS Feed (https://www.tvn-2.com/rss/)
2. GDELT Project DOC 2.0 API (Panama topics)
3. World Bank Open Data API (Panama and regional macro indicators)
4. USGS Earthquake Hazards Program GeoJSON API (Panama regional seismic box)
"""

import email.utils
import hashlib
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

logger = logging.getLogger(__name__)

USER_AGENT = "SentriaTVN-Copilot/1.0 (TVN Media HackIAthon Copilot; https://sentria-tvn.fly.dev)"


def _parse_rfc822_or_iso(date_str: str | None) -> str:
    """Normalize RFC 822 or ISO date string to ISO 8601 UTC."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed_tuple = email.utils.parsedate_to_datetime(date_str)
        return parsed_tuple.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _generate_article_id(url: str) -> str:
    """Generate a deterministic article ID from URL."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10].upper()
    return f"NOT-LIVE-{digest}"


class LiveDataFetcher:
    """Orchestrates periodic retrieval of real data from public APIs."""

    def __init__(self, timeout_seconds: float = 25.0) -> None:
        self.timeout = timeout_seconds

    async def fetch_tvn_rss(self, feed_url: str = "https://www.tvn-2.com/rss/") -> list[dict[str, Any]]:
        """Fetch and parse live RSS items from TVN Panama."""
        logger.info(f"Fetching TVN RSS feed from: {feed_url}")
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            resp = await client.get(feed_url)
            resp.raise_for_status()
            content = resp.text

        feed = feedparser.parse(content)
        records: list[dict[str, Any]] = []
        now_utc = datetime.now(timezone.utc).isoformat()

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            if not url:
                continue

            title = getattr(entry, "title", "Sin título").strip()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            pub_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
            iso_date = _parse_rfc822_or_iso(pub_date)

            # Extract possible section/topic from URL
            topic = "general"
            if "/economia/" in url:
                topic = "economia"
            elif "/nacionales/" in url:
                topic = "nacionales"
            elif "/judicial/" in url or "/seguridad/" in url:
                topic = "seguridad"
            elif "/mundo/" in url:
                topic = "internacional"

            records.append(
                {
                    "id_noticia": _generate_article_id(url),
                    "titulo": title,
                    "url": url,
                    "medio": "TVN Noticias",
                    "idioma": "es",
                    "fecha_publicacion": iso_date,
                    "fecha_deteccion": now_utc,
                    "fecha_extraccion": now_utc,
                    "tema": topic,
                    "origen": "rss",
                    "alcance_texto": "titular_metadatos",
                    "resumen": summary.strip()[:600],
                    "metadata": {
                        "source_feed": feed_url,
                        "tags": [t.get("term") for t in getattr(entry, "tags", []) if isinstance(t, dict)],
                    },
                }
            )

        logger.info(f"Fetched {len(records)} live news items from TVN RSS")
        return records

    async def fetch_gdelt(
        self,
        query: str = "panama (logistica OR turismo OR economia)",
        max_records: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch recent Panama news articles from GDELT DOC 2.0 API."""
        encoded_query = urllib.parse.quote(query)
        gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=artlist&maxrecords={max_records}&format=json"
        logger.info(f"Fetching GDELT articles: {gdelt_url}")

        records: list[dict[str, Any]] = []
        now_utc = datetime.now(timezone.utc).isoformat()

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.get(gdelt_url)
                if resp.status_code != 200:
                    logger.warning(f"GDELT returned HTTP {resp.status_code}")
                    return []

                content_type = resp.headers.get("content-type", "")
                if "json" not in content_type and not resp.text.strip().startswith("{"):
                    logger.warning(f"GDELT returned non-JSON response (possibly rate limit warning): {resp.text[:120]}")
                    return []

                data = resp.json()
                articles = data.get("articles", [])

                for art in articles:
                    url = art.get("url")
                    title = art.get("title", "").strip()
                    if not url or not title:
                        continue

                    # GDELT seendate is discovery time, not the article's publication time.
                    seen_date_raw = art.get("seendate")
                    if seen_date_raw:
                        try:
                            detected_at = datetime.strptime(seen_date_raw, "%Y%m%dT%H%M%SZ").replace(
                                tzinfo=timezone.utc
                            )
                            detected_at_iso = detected_at.isoformat()
                        except ValueError:
                            detected_at_iso = now_utc
                    else:
                        detected_at_iso = now_utc

                    domain = art.get("domain", "GDELT Source")
                    records.append(
                        {
                            "id_noticia": _generate_article_id(url),
                            "titulo": title,
                            "url": url,
                            "medio": domain,
                            "idioma": art.get("language", "es"),
                            "fecha_publicacion": "",
                            "fecha_deteccion": detected_at_iso,
                            "fecha_extraccion": now_utc,
                            "tema": "economia_logistica",
                            "origen": "gdelt",
                            "alcance_texto": "titular_metadatos",
                            "resumen": "",
                            "metadata": {
                                "sourcecountry": art.get("sourcecountry"),
                                "domain": domain,
                            },
                        }
                    )

                logger.info(f"Fetched {len(records)} live news items from GDELT")
        except Exception as exc:
            logger.warning(f"GDELT fetch encountered error: {exc}")

        return records

    async def fetch_world_bank(
        self,
        countries: list[str] | None = None,
        indicators: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch macro indicators from the World Bank API."""
        target_countries = countries or ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"]
        target_indicators = indicators or [
            "NY.GDP.MKTP.KD.ZG",  # GDP Growth %
            "FP.CPI.TOTL.ZG",  # Inflation CPI %
            "SL.UEM.TOTL.ZS",  # Unemployment %
            "SP.POP.TOTL",  # Total Population
        ]

        records: list[dict[str, Any]] = []
        now_utc = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            for country in target_countries:
                for indicator in target_indicators:
                    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date=2021:2024&format=json"
                    try:
                        resp = await client.get(url)
                        if resp.status_code != 200:
                            continue
                        data = resp.json()
                        if not isinstance(data, list) or len(data) < 2:
                            continue

                        entries = data[1]
                        if not isinstance(entries, list):
                            continue

                        for item in entries:
                            val = item.get("value")
                            date_year = item.get("date")
                            if date_year:
                                records.append(
                                    {
                                        "pais_iso3": country,
                                        "indicador_id": indicator,
                                        "anio": int(date_year),
                                        "valor": float(val) if val is not None else None,
                                        "unidad": "%" if "ZG" in indicator or "ZS" in indicator else "unidad",
                                        "fuente_url": url,
                                        "fecha_extraccion": now_utc,
                                        "licencia": "CC BY 4.0 (Banco Mundial)",
                                    }
                                )
                    except Exception as exc:
                        logger.warning(f"Error fetching WB {country}/{indicator}: {exc}")

        logger.info(f"Fetched {len(records)} indicators from World Bank API")
        return records

    async def fetch_usgs(
        self,
        min_magnitude: float = 3.0,
        bbox: tuple[float, float, float, float] = (5.0, 12.0, -86.0, -76.0),
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch seismic events in the Panama region box from USGS GeoJSON API."""
        min_lat, max_lat, min_lon, max_lon = bbox
        url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&minmagnitude={min_magnitude}"
            f"&minlatitude={min_lat}&maxlatitude={max_lat}"
            f"&minlongitude={min_lon}&maxlongitude={max_lon}"
            f"&limit={limit}"
        )
        logger.info(f"Fetching USGS seismic events: {url}")

        records: list[dict[str, Any]] = []
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0.0, 0.0, 0.0])

            lon = coords[0] if len(coords) > 0 else None
            lat = coords[1] if len(coords) > 1 else None
            depth = coords[2] if len(coords) > 2 else None

            records.append(
                {
                    "id": feat.get("id") or props.get("code", ""),
                    "magnitude": float(props.get("mag", 0.0)),
                    "place": props.get("place", "Región Panamá"),
                    "time": props.get("time", 0),
                    "updated": props.get("updated"),
                    "url": props.get("url", ""),
                    "latitud": lat,
                    "longitud": lon,
                    "profundidad": depth,
                    "status": props.get("status", "reviewed"),
                }
            )

        logger.info(f"Fetched {len(records)} seismic events from USGS API")
        return records

    async def sync_all(self, storage: SQLiteStorage) -> dict[str, Any]:
        """Execute all fetchers and persist data into SQLite storage with audit logs."""
        storage.init_db()
        results: dict[str, Any] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "sources": {},
        }

        # 1. TVN RSS
        t0 = datetime.now(timezone.utc).isoformat()
        try:
            tvn_items = await self.fetch_tvn_rss()
            count_tvn = storage.upsert_noticias(tvn_items)
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("tvn_rss", "SUCCESS", count_tvn, f"Ingested {count_tvn} items", t0, t1)
            results["sources"]["tvn_rss"] = {"status": "SUCCESS", "count": count_tvn}
        except Exception as exc:
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("tvn_rss", "ERROR", 0, str(exc), t0, t1)
            results["sources"]["tvn_rss"] = {"status": "ERROR", "error": str(exc)}

        # 2. GDELT
        t0 = datetime.now(timezone.utc).isoformat()
        try:
            gdelt_items = await self.fetch_gdelt()
            count_gdelt = storage.upsert_noticias(gdelt_items)
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("gdelt", "SUCCESS", count_gdelt, f"Ingested {count_gdelt} items", t0, t1)
            results["sources"]["gdelt"] = {"status": "SUCCESS", "count": count_gdelt}
        except Exception as exc:
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("gdelt", "ERROR", 0, str(exc), t0, t1)
            results["sources"]["gdelt"] = {"status": "ERROR", "error": str(exc)}

        # 3. World Bank Indicators
        t0 = datetime.now(timezone.utc).isoformat()
        try:
            wb_items = await self.fetch_world_bank()
            count_wb = storage.upsert_indicadores(wb_items)
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("world_bank", "SUCCESS", count_wb, f"Ingested {count_wb} indicators", t0, t1)
            results["sources"]["world_bank"] = {"status": "SUCCESS", "count": count_wb}
        except Exception as exc:
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("world_bank", "ERROR", 0, str(exc), t0, t1)
            results["sources"]["world_bank"] = {"status": "ERROR", "error": str(exc)}

        # 4. USGS Earthquakes
        t0 = datetime.now(timezone.utc).isoformat()
        try:
            usgs_items = await self.fetch_usgs()
            count_usgs = storage.upsert_eventos(usgs_items)
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("usgs", "SUCCESS", count_usgs, f"Ingested {count_usgs} events", t0, t1)
            results["sources"]["usgs"] = {"status": "SUCCESS", "count": count_usgs}
        except Exception as exc:
            t1 = datetime.now(timezone.utc).isoformat()
            storage.record_run("usgs", "ERROR", 0, str(exc), t0, t1)
            results["sources"]["usgs"] = {"status": "ERROR", "error": str(exc)}

        results["finished_at"] = datetime.now(timezone.utc).isoformat()
        results["db_stats"] = storage.get_stats()
        return results
