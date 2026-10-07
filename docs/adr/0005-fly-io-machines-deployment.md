# ADR-0005: Despliegue en Fly.io Machines con Docker Multi-Stage y Health Checks

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El repositorio debe estar preparado para su despliegue continuo en **Fly.io** según la guía oficial para agentes de IA (`https://fly.io/agent-ready.md`).
Requisitos técnicos clave para evitar los fallos más frecuentes en Fly.io:
* El servidor debe escuchar en `0.0.0.0` y nunca en `localhost`.
* El puerto interno configurado en `fly.toml` (`internal_port`) debe coincidir exactamente con el puerto donde corre la aplicación (`8080`).
* La imagen de contenedor debe construirse de forma eficiente y ligera.
* Las credenciales nunca deben comitearse en el código ni en `fly.toml`, sino suministrarse mediante secretos (`fly secrets set`).

## Decisión

1. **Construcción Multi-Stage en `Dockerfile`**:
   * Etapa de compilación/sincronización con imagen oficial `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`.
   * Ejecución de `uv sync --frozen --no-dev` para preparar el entorno virtual de producción.
   * Etapa final con `python:3.12-slim-bookworm`, creando un usuario no privilegiado (`appuser`) por seguridad.
2. **Configuración de `fly.toml`**:
   * `internal_port = 8080`.
   * Endpoint de monitoreo `/healthz` con chequeo HTTP cada 15 segundos.
   * Configuración de escalado a cero (`auto_stop_machines = "stop"`, `auto_start_machines = true`) para optimizar costos de máquina cuando no reciba peticiones.
3. **Flujo de Despliegue**:
   * Despliegue automatizado mediante GitHub Actions (`.github/workflows/fly-deploy.yml`) y comando manual `fly deploy`.

## Consecuencias

### Positivas
* Despliegue reproducible con tamaño mínimo de imagen (< 150MB).
* Arranque rápido de máquinas en regiones cercanas (ej. `iad` o `mia`).
* Trazabilidad de salud operativa mediante `/healthz`.
