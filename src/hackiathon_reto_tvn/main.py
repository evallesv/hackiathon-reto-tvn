"""Main entrypoint for HackIAthon Copilot FastAPI server."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hackiathon_reto_tvn.api.routes import router
from hackiathon_reto_tvn.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hackiathon_reto_tvn")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(
        f"Starting HackIAthon Copilot server | Env: {settings.ENVIRONMENT} | LLM Provider: {settings.LLM_PROVIDER}"
    )
    yield
    logger.info("Shutting down HackIAthon Copilot server")


def create_app() -> FastAPI:
    """Application factory for FastAPI app."""
    app = FastAPI(
        title="HackIAthon Copilot - De la señal a la decisión",
        description=(
            "Copiloto de inteligencia informativa y análisis de entorno con IA para TVN Media. "
            "Priorización explicable, verificación de evidencias y generación de borradores trazables."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()


def start() -> None:
    """Entry point for running uvicorn directly via CLI or script."""
    settings = get_settings()
    uvicorn.run(
        "hackiathon_reto_tvn.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )


if __name__ == "__main__":
    start()
