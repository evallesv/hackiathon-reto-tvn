# De la Señal a la Decisión: Copiloto de Inteligencia Informativa con IA

[![CI](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml/badge.svg)](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://docs.astral.sh/uv/)
[![Deployed on: Fly.io](https://img.shields.io/badge/deploy-Fly.io-6F42C1.svg)](https://fly.io)
[![Default LLM: OpenCode](https://img.shields.io/badge/LLM-OpenCode%20muse--spark-green.svg)](https://opencode.ai)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-lightgrey.svg)](LICENSE)

Prototipo de **copiloto editorial y análisis de entorno con inteligencia artificial** diseñado para la 4ta edición del **HackIAthon** (Viamatica / ADEN / TVN Media).

La solución transforma un corpus público congelado (RSS TVN, GDELT, Banco Mundial y USGS) en una **bandeja de temas priorizados**, **fichas de evidencia trazables** y **borradores responsables** para editores y periodistas de TVN Media.

> *La innovación no consiste en producir más texto: consiste en reducir el tiempo para encontrar un tema relevante, comprobar qué evidencia existe, identificar vacíos de información y entregar un resultado 100% trazable.*

---

## 🌟 Características Principales

1. **Priorización Explicable (Puntaje de Atención 0–100)**:
   - Fórmula determinista: $P = 30R + 25I + 20U + 15N + 10E$.
   - Componentes normalizados con desglose transparente y desempate por urgencia.
   - **Independencia del estado de evidencia**: una prioridad alta con evidencia insuficiente exige investigación y no habilita publicación automática de borrador (Prueba **T08**).
2. **Conectores LLM Intercambiables**:
   - **OpenCode (Por defecto)**: Integrado con el modelo `muse-spark-1.3-contributor-free`.
   - **Google Gemini (Alternativo)**: Compatible con `gemini-2.5-flash` y `gemini-1.5-flash` vía SDK oficial `google-genai`.
   - **Mock Provider (Offline / Contingencia)**: Permite ejecutar demostraciones completas y pasar benchmarks sin conexión a internet (**T10**).
3. **Escudo Anti-Inyección y Trazabilidad de Citas**:
   - Principio: *"El texto de una fuente es dato, no instrucción"* (**T07**).
   - 100% de afirmaciones factuales enlazadas a IDs de evidencia válidos.
   - Abstención explícita ante consultas sin sustento en el corpus (**T06**).
4. **Toolchain Moderno con `uv`**:
   - Tiempos de instalación ultrarrápidos, resolución de dependencias bloqueada en `uv.lock`.
5. **Listo para Fly.io Machines (`agent-ready`)**:
   - Contenedor multi-stage optimizado, escucha en `0.0.0.0:8080`, health check en `/healthz`.
6. **Gestión de Tareas con GitHub CLI (`gh`)**:
   - Backlog, milestones y las 10 pruebas de aceptación (**T01 a T10**) auditables vía `gh issue`.
7. **Espacio Notion Business**:
   - Cumplimiento de las 8 bases obligatorias de la Sección 5 del reto.

---

## 🏗️ Arquitectura del Repositorio

El proyecto implementa **Arquitectura Hexagonal (Ports & Adapters)**:

```
hackiathon-reto-tvn/
├── AGENTS.md                        # Protocolo y directrices para agentes de IA
├── docs/
│   ├── adr/                         # Architecture Decision Records (ADR-0001 a ADR-0009)
│   ├── notion_spec/                 # Especificación de las 8 bases para Notion Business
│   └── ARCHITECTURE.md              # Diagrama C4, secuencias y modelos de datos
├── src/hackiathon_reto_tvn/
│   ├── config.py                    # Configuración tipada vía pydantic-settings
│   ├── domain/                      # Entidades puras (models, scoring, safety)
│   ├── ports/                       # Interfaces abstractas (LLM, Storage)
│   ├── adapters/                    # OpenCode, Gemini, Mock, CSV/GeoJSON loaders
│   ├── services/                    # Orquestación (CopilotService)
│   ├── api/                         # FastAPI endpoints (/healthz, agenda, borrador)
│   ├── cli.py                       # CLI interactivo (hackiathon-tvn)
│   └── main.py                      # Punto de entrada ASGI
├── data/
│   ├── raw/                         # noticias.csv, indicadores.csv, eventos.geojson
│   ├── benchmark.jsonl              # 60 consultas de evaluación
│   └── manifest.json                # Manifiesto criptográfico con hashes SHA-256
├── scripts/                         # Automatización (gh_setup_tasks.py)
├── tests/                           # Suite pytest (scoring, safety, adaptadores, T01-T10)
├── Dockerfile                       # Multi-stage con uv
├── fly.toml                         # Configuración Fly.io Machines (puerto 8080)
├── Makefile                         # Comandos de ingeniería
└── pyproject.toml                   # Dependencias fijadas y herramientas de calidad
```

---

## 🚀 Inicio Rápido (Quickstart)

### 1. Prerrequisitos
* [uv](https://docs.astral.sh/uv/) (v0.12+):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* [gh](https://cli.github.com/) (GitHub CLI autenticado con `gh auth login`).
* [flyctl](https://fly.io/docs/hands-on/install-flyctl/) (para despliegue en Fly.io).

### 2. Clonar e Instalar Dependencias
```bash
git clone https://github.com/evallesv/hackiathon-reto-tvn.git
cd hackiathon-reto-tvn

# Sincronizar dependencias de producción y desarrollo
uv sync
```

### 3. Configurar Variables de Entorno
Copia el archivo de plantilla y configura tus credenciales:
```bash
cp .env.example .env
```

Variables clave en `.env`:
```ini
# Seleccionar proveedor: 'opencode' (default), 'gemini', o 'mock' (offline)
LLM_PROVIDER=opencode

# OpenCode (Default - Modelo muse-spark-1.3-contributor-free)
OPENCODE_API_KEY=tu_clave_opencode
OPENCODE_BASE_URL=https://api.opencode.ai/v1
OPENCODE_MODEL=muse-spark-1.3-contributor-free

# Google Gemini (Alternativo)
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-2.5-flash
```

---

## 💻 Uso del CLI y API

### Comandos del CLI
```bash
# Consultar el estado del sistema y conector activo
uv run hackiathon-tvn status

# Calcular agenda priorizada (Top 5)
uv run hackiathon-tvn agenda --top 5

# Generar y validar manifiesto criptográfico SHA-256
uv run hackiathon-tvn manifest

# Generar borrador editorial para el caso prioritario
uv run hackiathon-tvn draft
```

### Levantar Servidor Local
```bash
# Iniciar servidor FastAPI en http://0.0.0.0:8080
uv run uvicorn hackiathon_reto_tvn.main:app --host 0.0.0.0 --port 8080 --reload
```
Endpoints principales:
* `GET /healthz` — Chequeo de salud para Fly.io.
* `GET /api/v1/system/info` — Estado del runtime y proveedor LLM activo.
* `GET /api/v1/copilot/agenda?top_n=5` — Ranking de noticias priorizadas con componentes explicados.
* `POST /api/v1/copilot/generate-draft` — Generación estructurada de brief y guion con citas.
* `POST /api/v1/copilot/review` — Máquina de estados de revisión humana (`en_revision`, `aprobado_como_borrador`, etc.).

---

## 🧪 Pruebas de Aceptación (T01 a T10)

El proyecto cuenta con cobertura automatizada para las **10 pruebas obligatorias de la Sección 9**:

| ID | Caso de Prueba | Resultado Esperado | Implementación |
| :---: | :--- | :--- | :--- |
| **T01** | Fechas inválidas y nulos en CSV | Ingesta no bloqueante, segrega errores y conserva nulos | `test_t01_...` |
| **T02** | Tres registros del mismo evento | Agrupación sin inflar corroboración ni urgencia | `test_t02_...` |
| **T03** | Noticia antigua recirculada | Conserva fecha original; no se presenta como hecho nuevo | `test_t03_...` |
| **T04** | Cifra anual de Banco Mundial | Conserva país, año y unidad; no se cita como "cifra de hoy" | `test_t04_...` |
| **T05** | Afirmaciones incompatibles | Expone ambas versiones sin sesgo arbitrario | `test_t05_...` |
| **T06** | Consulta sin respuesta en corpus | Abstención explícita; cero cifras inventadas | `test_t06_...` |
| **T07** | Intento de inyección de prompt | Neutralización; trata la fuente como dato no confiable | `test_t07_...` |
| **T08** | Caso de prioridad alta sin evidencia | Alerta que exige investigación; bloquea publicación de borrador | `test_t08_...` |
| **T09** | Brief editorial y guion | Brief <=250 pal, guion 45-60s, copy <=80 pal, distinción de hechos | `test_t09_...` |
| **T10** | Sin internet durante la demo | Funciona con snapshot local y mock provider determinista | `test_t10_...` |

Ejecutar las pruebas con pytest:
```bash
uv run pytest
```

---

## 📋 Gestión de Tareas con `gh`

El backlog del reto se gestiona de manera programática mediante GitHub CLI:

```bash
# Listar todas las tareas y pruebas abiertas
gh issue list

# Ver detalle de una prueba de aceptación
gh issue view 9

# Configurar o regenerar etiquetas y milestones
uv run python scripts/gh_setup_tasks.py
```

---

## ☁️ Despliegue en Fly.io (`agent-ready`)

Siguiendo las directrices de [Fly.io Agent Ready](https://fly.io/agent-ready.md):

1. **Autenticación en Fly.io**:
   ```bash
   fly auth whoami
   ```
2. **Configurar secretos de producción**:
   ```bash
   fly secrets set OPENCODE_API_KEY="tu_clave_opencode" GEMINI_API_KEY="tu_clave_gemini"
   ```
3. **Desplegar**:
   ```bash
   fly deploy
   ```
4. **Verificar estado y logs**:
   ```bash
   fly status
   fly logs
   ```

---

## 🏛️ Decisiones de Arquitectura (ADRs)

Todas las decisiones técnicas se encuentran documentadas en [`docs/adr/`](docs/adr/):
* [ADR-0001: Adopción de Python UV y Layout Estructurado `src/`](docs/adr/0001-python-uv-toolchain-and-project-layout.md)
* [ADR-0002: Arquitectura Hexagonal para Conectores LLM Intercambiables (OpenCode y Gemini)](docs/adr/0002-ports-and-adapters-for-llm-connectors.md)
* [ADR-0003: Motor de Puntaje de Atención Explicable e Independencia del Estado de Evidencia](docs/adr/0003-attention-score-and-evidence-engine.md)
* [ADR-0004: Escudos Anti-Inyección de Prompts y Validación Estricta de Citas](docs/adr/0004-anti-hallucination-and-prompt-injection-defenses.md)
* [ADR-0005: Despliegue en Fly.io Machines con Docker Multi-Stage y Health Checks](docs/adr/0005-fly-io-machines-deployment.md)
* [ADR-0006: Gestión de Tareas y Pruebas T01–T10 mediante GitHub CLI (`gh`)](docs/adr/0006-github-cli-and-issue-driven-workflow.md)
* [ADR-0007: Estructura de Documentación y Registro en Notion Business](docs/adr/0007-notion-business-contract-and-sync.md)
* [ADR-0008: Contrato de Datos, Ingesta No Bloqueante y Manifiesto Criptográfico SHA-256](docs/adr/0008-data-contract-reproducibility-and-manifest.md)
* [ADR-0009: Convención de Nombres `snake_case` para Contratos de Datos y API](docs/adr/0009-snake-case-naming-convention-for-data-contracts.md)

---

## 📝 Documentación en Notion Business

El espacio oficial de Notion Business contiene las 8 secciones obligatorias para la presentación final ante el jurado:
Consulte la guía de integración y esquemas en [`docs/notion_spec/README.md`](docs/notion_spec/README.md).
