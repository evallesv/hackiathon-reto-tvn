# syntax=docker/dockerfile:1
# ==============================================================================
# Multi-stage Dockerfile optimized with uv for Fly.io Machines deployment
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependencies Resolution
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and frozen uv dependencies
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency definition files first for optimal Docker layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only into .venv
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install project package
COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev

# ------------------------------------------------------------------------------
# Stage 2: Minimal Runtime Environment
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Configure runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8080 \
    HOST=0.0.0.0

# Create an unprivileged user for security compliance
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy virtual environment and source tree from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src
COPY --from=builder --chown=appuser:appgroup /app/README.md /app/README.md

# Copy default frozen dataset directory
COPY --chown=appuser:appgroup data /app/data

# Switch to unprivileged user
USER appuser

# Expose Fly.io target internal port (8080)
EXPOSE 8080

# Fly.io health check requirement: must bind to 0.0.0.0 on internal_port
CMD ["uvicorn", "hackiathon_reto_tvn.main:app", "--host", "0.0.0.0", "--port", "8080"]
