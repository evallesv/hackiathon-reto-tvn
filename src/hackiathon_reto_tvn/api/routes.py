"""FastAPI routing endpoints for HackIAthon Copilot."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.domain.models import (
    BorradorBancario,
    BorradorEditorial,
    EstadoRevision,
    FichaCaso,
    Manifest,
    QueryRequest,
    QueryResponse,
)
from hackiathon_reto_tvn.services.copilot_service import CopilotService

router = APIRouter()


class SystemInfoResponse(BaseModel):
    app_name: str = "hackiathon-reto-tvn"
    status: str = "healthy"
    environment: str
    llm_provider: str
    llm_model: str
    decision_provider: str = ""
    decision_model: str = ""
    raw_data_dir: str


class ReviewUpdateRequest(BaseModel):
    caso_id: str
    nuevo_estado: EstadoRevision
    persona_revisora: str
    observaciones: Optional[str] = None


class ContradictionRequest(BaseModel):
    texto_a: str = Field(..., description="Primera versión o afirmación")
    texto_b: str = Field(..., description="Segunda versión o afirmación")


class GenerateDraftRequest(BaseModel):
    """Identifies a server-resolved case; client evidence and scores are never accepted."""

    caso_id: str


def get_copilot_service(settings: Settings = Depends(get_settings)) -> CopilotService:
    return CopilotService(settings=settings)


@router.get("/healthz", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def health_check(settings: Settings = Depends(get_settings)) -> Dict[str, str]:
    """Health check endpoint required by Fly.io agent-ready specification."""
    return {
        "status": "healthy",
        "service": "hackiathon-reto-tvn",
        "provider": settings.LLM_PROVIDER,
        "decision_provider": settings.DECISION_PROVIDER,
    }


@router.get("/api/v1/system/info", response_model=SystemInfoResponse, tags=["System"])
async def system_info(
    service: CopilotService = Depends(get_copilot_service),
    settings: Settings = Depends(get_settings),
) -> SystemInfoResponse:
    """Returns runtime system status, active LLM configuration, and active decision model."""
    return SystemInfoResponse(
        environment=settings.ENVIRONMENT,
        llm_provider=service.llm.provider_name,
        llm_model=service.llm.model_name,
        decision_provider=service.decision_client.provider_name,
        decision_model=service.decision_client.model_name,
        raw_data_dir=str(settings.RAW_DATA_DIR),
    )


@router.get("/api/v1/copilot/agenda", response_model=List[FichaCaso], tags=["Copilot"])
async def get_agenda(
    top_n: int = Query(5, ge=1, le=20),
    service: CopilotService = Depends(get_copilot_service),
) -> List[FichaCaso]:
    """Retrieves prioritized agenda of news events ranked by attention score (CU-01)."""
    return await service.prioritize_agenda_async(top_n=top_n)


@router.post("/api/v1/copilot/contradictions", tags=["Copilot"])
async def check_contradictions(
    req: ContradictionRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> Dict[str, Any]:
    """Evaluates whether two statements contain factual contradictions using the decision model (T05)."""
    return await service.detect_contradictions(req.texto_a, req.texto_b)


@router.post("/api/v1/copilot/generate-draft", response_model=BorradorEditorial, tags=["Copilot"])
async def generate_draft(
    req: GenerateDraftRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> BorradorEditorial:
    """Generates a package for a case resolved from the server's current corpus."""
    try:
        caso = await service.get_agenda_case(req.caso_id)
        if caso is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado en la agenda actual.")
        borrador = await service.generate_tvn_editorial_package(caso)
        return borrador
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/api/v1/copilot/generate-banking-draft", response_model=BorradorBancario, tags=["Copilot"])
async def generate_banking_draft(
    req: GenerateDraftRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> BorradorBancario:
    """Generates an economic and logistics environment bulletin for banking analysts (CU-05)."""
    try:
        caso = await service.get_agenda_case(req.caso_id)
        if caso is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado en la agenda actual.")
        borrador = await service.generate_banking_bulletin(caso)
        return borrador
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/api/v1/copilot/query", response_model=QueryResponse, tags=["Copilot"])
async def query_copilot(
    req: QueryRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> QueryResponse:
    """Answers analytical or editorial questions with citations or explicit abstention (T04, T05, T06, T07)."""
    return await service.answer_query_async(consulta=req.consulta, modalidad=req.modalidad)


@router.get("/api/v1/copilot/fichas", response_model=List[FichaCaso], tags=["Copilot"])
async def get_fichas(
    settings: Settings = Depends(get_settings),
) -> List[FichaCaso]:
    """Retrieves all tracked case cards (fichas) from persistent SQLite storage (CU-02)."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()
    fichas_raw = storage.get_all_fichas()
    if not fichas_raw:
        seed_path = settings.DATA_DIR / "fichas.jsonl"
        if seed_path.exists():
            storage.seed_fichas_from_jsonl(seed_path)
            fichas_raw = storage.get_all_fichas()
    return [FichaCaso.model_validate(f) for f in fichas_raw]


@router.get("/api/v1/copilot/fichas/export", tags=["Copilot"])
async def export_fichas(
    settings: Settings = Depends(get_settings),
) -> List[Dict[str, Any]]:
    """Exports all case cards as a list of dictionaries for downstream auditing."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()
    fichas_raw = storage.get_all_fichas()
    if not fichas_raw:
        seed_path = settings.DATA_DIR / "fichas.jsonl"
        if seed_path.exists():
            storage.seed_fichas_from_jsonl(seed_path)
            fichas_raw = storage.get_all_fichas()
    return fichas_raw


@router.get("/api/v1/copilot/fichas/{id_caso}", response_model=FichaCaso, tags=["Copilot"])
async def get_ficha_by_id(
    id_caso: str,
    settings: Settings = Depends(get_settings),
) -> FichaCaso:
    """Retrieves a single case card by ID."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()
    raw = storage.get_ficha(id_caso)
    if not raw:
        seed_path = settings.DATA_DIR / "fichas.jsonl"
        if seed_path.exists():
            storage.seed_fichas_from_jsonl(seed_path)
            raw = storage.get_ficha(id_caso)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ficha {id_caso} no encontrada.",
        )
    return FichaCaso.model_validate(raw)


@router.post("/api/v1/copilot/review", response_model=FichaCaso, tags=["Human-in-the-loop"])
async def update_review(
    req: ReviewUpdateRequest,
    service: CopilotService = Depends(get_copilot_service),
    settings: Settings = Depends(get_settings),
) -> FichaCaso:
    """Transitions a case through human review states and persists the decision in SQLite."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()

    existing = storage.get_ficha(req.caso_id)
    if existing:
        updated_dict = storage.update_review_status(
            id_caso=req.caso_id,
            nuevo_estado=req.nuevo_estado.value,
            persona_revisora=req.persona_revisora,
            observaciones=req.observaciones,
        )
        if updated_dict:
            return FichaCaso.model_validate(updated_dict)

    agenda = await service.prioritize_agenda_async(top_n=20)
    for c in agenda:
        if c.id_caso == req.caso_id:
            updated = service.update_human_review(
                caso=c,
                nuevo_estado=req.nuevo_estado,
                persona_revisora=req.persona_revisora,
                observaciones=req.observaciones,
            )
            storage.upsert_ficha(updated)
            return updated

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Caso {req.caso_id} no encontrado en la base de datos ni en la agenda actual.",
    )


@router.get("/api/v1/copilot/manifest", response_model=Manifest, tags=["Data"])
async def get_manifest(
    service: CopilotService = Depends(get_copilot_service),
) -> Manifest:
    """Returns reproducibility manifest with SHA-256 hashes."""
    manifest_path = service.settings.DATA_DIR / "manifest.json"
    if manifest_path.exists():
        import json

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Manifest.model_validate(data)

    return service.repo.generate_manifest(service.settings.DATA_DIR)


@router.get("/api/v1/ingestion/status", tags=["Live Ingestion"])
async def get_ingestion_status(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Returns status and statistics of the SQLite storage and periodic ingestion."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()
    stats = storage.get_stats()
    stats["ingestion_enabled"] = settings.INGESTION_ENABLED
    stats["interval_minutes"] = settings.INGESTION_INTERVAL_MINUTES
    return stats


@router.post("/api/v1/ingestion/trigger", tags=["Live Ingestion"])
async def trigger_ingestion(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Manually triggers an on-demand live data ingestion cycle."""
    from hackiathon_reto_tvn.services.ingestion_scheduler import run_ingestion_cycle

    result = await run_ingestion_cycle(settings)
    return result


@router.get("/api/v1/ingestion/noticias", tags=["Live Ingestion"])
async def get_live_noticias(
    limit: int = Query(default=20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
) -> List[Dict[str, Any]]:
    """Returns the latest live news records stored in SQLite."""
    from hackiathon_reto_tvn.adapters.data.sqlite_storage import SQLiteStorage

    storage = SQLiteStorage(settings.SQLITE_DB_PATH)
    storage.init_db()
    return storage.get_latest_noticias(limit=limit)


@router.get("/api/v1/copilot/benchmark/metrics", tags=["Copilot"])
async def get_benchmark_metrics(
    service: CopilotService = Depends(get_copilot_service),
) -> Dict[str, Any]:
    """Returns official evaluation benchmark metrics and comparative baseline results (Sección 8 & 9.1)."""
    from hackiathon_reto_tvn.services.baseline_evaluator import BaselineEvaluator

    evaluator = BaselineEvaluator(service=service, settings=service.settings)
    return await evaluator.run_benchmark_suite(only_dev=True)
