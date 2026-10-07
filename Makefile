# ==============================================================================
# Makefile - HackIAthon TVN Media Engineering Automation
# ==============================================================================

.PHONY: help install sync lint format format-check typecheck test check run cli docker-build docker-run fly-status fly-deploy manifest

help:
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar uv y sincronizar dependencias de desarrollo"
	@echo "  make sync          - Sincronizar dependencias bloqueadas con uv sync"
	@echo "  make lint          - Ejecutar ruff check"
	@echo "  make format        - Formatear código con ruff format"
	@echo "  make format-check  - Verificar formato sin modificar archivos"
	@echo "  make typecheck     - Verificar tipos estáticos con mypy"
	@echo "  make check         - Gate completo: ruff + format-check + mypy + pytest (ejecutar antes de terminar)"
	@echo "  make test          - Ejecutar suite completa con pytest y cobertura"
	@echo "  make run           - Levantar servidor FastAPI localmente en puerto 8080"
	@echo "  make cli           - Ver estado del CLI del copiloto"
	@echo "  make manifest      - Regenerar manifest.json con hashes SHA-256"
	@echo "  make docker-build  - Construir imagen Docker de producción"
	@echo "  make docker-run    - Correr contenedor Docker local en puerto 8080"
	@echo "  make fly-status    - Consultar estado de máquinas en Fly.io"
	@echo "  make fly-deploy    - Desplegar en Fly.io Machines"

install:
	uv sync

sync:
	uv sync --frozen

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src/

test:
	uv run pytest

check: lint format-check typecheck test

run:
	uv run uvicorn hackiathon_reto_tvn.main:app --host 0.0.0.0 --port 8080 --reload

cli:
	uv run hackiathon-tvn status

manifest:
	uv run hackiathon-tvn manifest

docker-build:
	docker build -t hackiathon-reto-tvn:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env hackiathon-reto-tvn:latest

fly-status:
	fly status

fly-deploy:
	fly deploy
