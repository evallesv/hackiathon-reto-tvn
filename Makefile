# ==============================================================================
# Makefile - HackIAthon TVN Media Engineering Automation
# ==============================================================================

.PHONY: help install sync lint format format-check typecheck test check run cli docker-build docker-run fly-status fly-deploy manifest setup-hooks benchmark audit-snapshot prepare-snapshot sqlite-snapshot

SNAPSHOT_DIR ?= data
CANDIDATE_DIR ?= /private/tmp/hackiathon-snapshot-candidate

help:
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar uv, sincronizar dependencias y configurar git hooks"
	@echo "  make sync          - Sincronizar dependencias bloqueadas con uv sync"
	@echo "  make setup-hooks   - Configurar git hooks locales (protección de rama main)"
	@echo "  make lint          - Ejecutar ruff check"
	@echo "  make format        - Formatear código con ruff format"
	@echo "  make format-check  - Verificar formato sin modificar archivos"
	@echo "  make typecheck     - Verificar tipos estáticos con mypy"
	@echo "  make check         - Gate completo: ruff + format-check + mypy + pytest (ejecutar antes de terminar)"
	@echo "  make test          - Ejecutar suite completa con pytest y cobertura"
	@echo "  make benchmark     - Ejecutar suite de evaluación de 60 consultas y baselines de IA"
	@echo "  make run           - Levantar servidor FastAPI localmente en puerto 8080"
	@echo "  make cli           - Ver estado del CLI del copiloto"
	@echo "  make manifest      - Regenerar manifest.json con hashes SHA-256"
	@echo "  make audit-snapshot - Auditar cobertura y hashes de una carpeta snapshot (sin escribir)"
	@echo "  make prepare-snapshot - Crear snapshot temporal (solo se publica si cumple todos los mínimos)"
	@echo "  make sqlite-snapshot - Empaquetar el corpus congelado como snapshot SQLite de solo lectura"
	@echo "  make docker-build  - Construir imagen Docker de producción"
	@echo "  make docker-run    - Correr contenedor Docker local en puerto 8080"
	@echo "  make fly-status    - Consultar estado de máquinas en Fly.io"
	@echo "  make fly-deploy    - Desplegar en Fly.io Machines"

install:
	uv sync
	@$(MAKE) setup-hooks

setup-hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "Git hooks locales configurados exitosamente en .githooks/."

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

benchmark:
	uv run python scripts/run_benchmark.py

audit-snapshot:
	uv run python scripts/audit_snapshot.py --data-dir "$(SNAPSHOT_DIR)"

prepare-snapshot:
	uv run python scripts/prepare_snapshot.py --output-dir "$(CANDIDATE_DIR)"

sqlite-snapshot:
	uv run python scripts/build_sqlite_snapshot.py

check: lint format-check typecheck test

run:
	uv run uvicorn hackiathon_reto_tvn.main:app --host 0.0.0.0 --port 8080 --reload

status:
	uv run python -c "from hackiathon_reto_tvn.config import get_settings; s = get_settings(); print(f'Env: {s.ENVIRONMENT} | LLM: {s.LLM_PROVIDER} | Decision: {s.DECISION_PROVIDER} | Port: {s.PORT}')"

manifest:
	uv run python -c "from hackiathon_reto_tvn.adapters.data.loaders import LocalStorageRepository; from hackiathon_reto_tvn.config import get_settings; r = LocalStorageRepository(); cfg = get_settings(); m = r.generate_manifest(cfg.DATA_DIR); print(f'Manifiesto SHA-256 verificado exitosamente con {len(m.archivos)} archivos.')"

docker-build:
	docker build -t hackiathon-reto-tvn:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env hackiathon-reto-tvn:latest

deploy:
	gh workflow run fly-deploy.yml
