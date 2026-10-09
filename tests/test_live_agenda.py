"""Tests for choosing recent live news while retaining a clearly labeled frozen fallback."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.api.routes import get_copilot_service, get_settings
from hackiathon_reto_tvn.config import Settings
from hackiathon_reto_tvn.domain.models import EstadoRevision
from hackiathon_reto_tvn.main import app
from hackiathon_reto_tvn.services.copilot_service import CopilotService


def _service(tmp_path: Path) -> tuple[CopilotService, SQLiteStorage]:
    db_path = tmp_path / "copilot.db"
    settings = Settings(
        ENVIRONMENT="development",
        DATA_DIR=Path("data"),
        RAW_DATA_DIR=Path("data/raw"),
        SQLITE_DB_PATH=db_path,
        DECISION_PROVIDER="mock",
        LLM_PROVIDER="mock",
    )
    storage = SQLiteStorage(db_path)
    storage.init_db()
    service = CopilotService(
        settings=settings,
        llm_client=MockLLMAdapter(),
        decision_client=MockDecisionAdapter(),
    )
    return service, storage


def test_agenda_prefers_live_news_within_90_day_window(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    published = (datetime.now(timezone.utc) - timedelta(days=89)).isoformat()
    storage.upsert_noticias(
        [
            {
                "id_noticia": "NOT-LIVE-001",
                "titulo": "Actualización reciente sobre el Canal de Panamá",
                "url": "https://example.com/live-001",
                "medio": "TVN Noticias",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
                "fecha_extraccion": published,
                "tema": "logistica_canal",
                "origen": "tvn_rss",
            }
        ]
    )

    [case] = service.prioritize_agenda(top_n=1)

    assert case.origen_datos == "ingesta_viva"
    assert case.fecha_actualizacion_fuente == published
    assert case.ids_fuente == ["NOT-LIVE-001"]
    assert case.id_caso.startswith("CASO-LIVE-")
    assert service.prioritize_agenda(top_n=1)[0].id_caso == case.id_caso


def test_agenda_uses_labeled_snapshot_when_live_news_is_stale(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    stale = (datetime.now(timezone.utc) - timedelta(days=91)).isoformat()
    storage.upsert_noticias(
        [
            {
                "id_noticia": "NOT-STALE-001",
                "titulo": "Noticia viva antigua sobre el Canal",
                "url": "https://example.com/stale-001",
                "fecha_publicacion": stale,
                "fecha_deteccion": stale,
            }
        ]
    )

    agenda = service.prioritize_agenda(top_n=1)

    assert agenda
    assert agenda[0].origen_datos == "snapshot_congelado"
    assert not agenda[0].id_caso.startswith("CASO-LIVE-")


async def test_editorial_query_searches_live_news_before_historical_snapshot(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    published = datetime.now(timezone.utc).isoformat()
    storage.upsert_noticias(
        [
            {
                "id_noticia": "NOT-LIVE-QUERY",
                "titulo": "Autoridad anuncia cierre temporal del puerto nacional",
                "url": "https://example.com/live-query",
                "medio": "TVN Noticias",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
            }
        ]
    )

    response = await service.answer_query_async("¿Qué sabemos del cierre temporal del puerto?")

    assert not response.es_abstencion
    assert response.citas[0]["id_fuente"] == "NOT-LIVE-QUERY"


async def test_editorial_query_uses_live_world_bank_observation(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    storage.upsert_indicadores(
        [
            {
                "pais_iso3": "PAN",
                "indicador_id": "NY.GDP.MKTP.KD.ZG",
                "anio": 2024,
                "valor": 5.7,
                "unidad": "%",
                "fuente_url": "https://api.worldbank.org/live-gdp",
                "fecha_extraccion": datetime.now(timezone.utc).isoformat(),
                "licencia": "CC BY 4.0",
            }
        ]
    )

    response = await service.answer_query_async("¿Cuál fue el PIB de Panamá en 2024?")

    assert "5.7%" in response.respuesta
    assert response.citas[0]["url_fuente"] == "https://api.worldbank.org/live-gdp"


async def test_editorial_query_uses_live_usgs_event(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    storage.upsert_eventos(
        [
            {
                "id": "us7000m1a1-live",
                "magnitude": 4.8,
                "place": "Golfo de Burica, Panamá",
                "time": 1_800_000_000_000,
                "url": "https://earthquake.usgs.gov/live-event",
                "latitud": 7.0,
                "longitud": -82.0,
                "profundidad": 18.0,
                "status": "reviewed",
            }
        ]
    )

    response = await service.answer_query_async("¿Qué reportó USGS sobre el último sismo de Burica?")

    assert "4.8" in response.respuesta
    assert response.citas[0]["id_fuente"] == "us7000m1a1-live"


def test_agenda_restores_persisted_human_review_on_refresh(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    published = datetime.now(timezone.utc).isoformat()
    storage.upsert_noticias(
        [
            {
                "id_noticia": "NOT-LIVE-REVIEW",
                "titulo": "Autoridad anuncia investigación de infraestructura crítica",
                "url": "https://example.com/live-review",
                "medio": "TVN Noticias",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
            }
        ]
    )
    [first_case] = service.prioritize_agenda(top_n=1)
    first_case.estado_revision = EstadoRevision.REQUIERE_EVIDENCIA
    first_case.persona_revisora = "Editora de turno"
    first_case.observaciones_revision = "Solicitar versión oficial"
    storage.upsert_ficha(first_case)

    [refreshed_case] = service.prioritize_agenda(top_n=1)

    assert refreshed_case.estado_revision == EstadoRevision.REQUIERE_EVIDENCIA
    assert refreshed_case.persona_revisora == "Editora de turno"
    assert refreshed_case.observaciones_revision == "Solicitar versión oficial"


def test_fichas_api_includes_live_agenda_cases(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    published = datetime.now(timezone.utc).isoformat()
    storage.upsert_noticias(
        [
            {
                "id_noticia": "NOT-LIVE-FICHAS",
                "titulo": "Autoridad investiga interrupción de servicio público",
                "url": "https://example.com/live-fichas",
                "medio": "TVN Noticias",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
            }
        ]
    )
    app.dependency_overrides[get_settings] = lambda: service.settings
    app.dependency_overrides[get_copilot_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/copilot/fichas")
            assert response.status_code == 200
            live_case = next(item for item in response.json() if item["origen_datos"] == "ingesta_viva")
            detail = client.get(f"/api/v1/copilot/fichas/{live_case['id_caso']}")
    finally:
        app.dependency_overrides.clear()

    assert detail.status_code == 200
    assert detail.json()["id_caso"] == live_case["id_caso"]
