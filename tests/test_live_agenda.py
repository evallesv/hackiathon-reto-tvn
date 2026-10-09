"""Tests for choosing recent live news while retaining a clearly labeled frozen fallback."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage
from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter
from hackiathon_reto_tvn.adapters.llm.mock_adapter import MockLLMAdapter
from hackiathon_reto_tvn.config import Settings
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


def test_agenda_prefers_recent_live_news_over_frozen_corpus(tmp_path: Path) -> None:
    service, storage = _service(tmp_path)
    published = datetime.now(timezone.utc).isoformat()
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
    stale = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
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
