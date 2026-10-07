# ADR-0001: Adopción de Python UV y Layout Estructurado `src/`

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El desarrollo de prototipos rápidos para hackathons suele sufrir por tiempos lentos de instalación, dependencias inconsistentes entre entornos locales y servidores, y problemas de empaquetado cuando se mezclan scripts con módulos ejecutables.
Para este reto se requiere una velocidad de iteración extrema, soporte nativo de Python 3.12+, aislamiento determinista y compatibilidad directa con contenedores Docker en Fly.io.

## Decisión

1. **Adopción exclusiva de `uv`** como gestor de paquetes y entornos virtuales.
2. Uso de archivo único `pyproject.toml` con grupos de dependencias (`dependencies` para producción y `dependency-groups.dev` para linters y tests).
3. Estructura de paquete bajo `src/hackiathon_reto_tvn/` para evitar colisiones de importación y forzar pruebas sobre el paquete instalado.
4. Bloqueo determinista mediante `uv.lock` versionado en el repositorio Git.

## Consecuencias

### Positivas
* Instalación y resolución de dependencias de 10x a 100x más rápida que `pip` o `poetry`.
* Reproducibilidad exacta en entornos locales macOS, Linux y en las imágenes Docker de Fly.io.
* Facilidad de ejecución sin activar virtualenv manualmente vía `uv run <comando>`.

### Negativas / Compromisos
* Los colaboradores deben tener instalado `uv` en sus estaciones de trabajo (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
