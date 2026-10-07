"""FastAPI routing endpoints for HackIAthon Copilot."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.domain.models import (
    BorradorEditorial,
    EstadoRevision,
    FichaCaso,
    Manifest,
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


class QueryRequest(BaseModel):
    consulta: str = Field(..., description="Pregunta del usuario o jurado")
    modalidad: str = "tvn_editorial"


class QueryResponse(BaseModel):
    consulta: str
    respuesta: str
    es_abstencion: bool
    citas: List[Dict[str, Any]] = Field(default_factory=list)


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
    caso: FichaCaso,
    service: CopilotService = Depends(get_copilot_service),
) -> BorradorEditorial:
    """Generates a complete TVN editorial package with citations for a given case."""
    try:
        borrador = await service.generate_tvn_editorial_package(caso)
        return borrador
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/api/v1/copilot/review", response_model=FichaCaso, tags=["Human-in-the-loop"])
async def update_review(
    req: ReviewUpdateRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> FichaCaso:
    """Transitions a case through human review states."""
    # Find case in agenda
    agenda = await service.prioritize_agenda_async(top_n=20)
    for c in agenda:
        if c.id_caso == req.caso_id:
            updated = service.update_human_review(
                caso=c,
                nuevo_estado=req.nuevo_estado,
                persona_revisora=req.persona_revisora,
                observaciones=req.observaciones,
            )
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Caso {req.caso_id} no encontrado en la agenda actual.",
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
