# De la Señal a la Decisión: Copiloto de Inteligencia Informativa con IA

[![CI](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml/badge.svg)](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://docs.astral.sh/uv/)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)
[![Decision Model: Cloudflare Clef](https://img.shields.io/badge/Decision%20Model-Cloudflare%20Clef-F38020.svg)](https://developers.cloudflare.com/workers-ai/)
[![Default LLM: OpenCode](https://img.shields.io/badge/LLM-OpenCode%20muse--spark-green.svg)](https://opencode.ai)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-lightgrey.svg)](LICENSE)


Prototipo de **copiloto editorial y análisis de entorno con inteligencia artificial** diseñado para la 4ta edición del **HackIAthon** (Viamatica / ADEN / TVN Media).

La solución transforma un corpus público congelado (RSS TVN, GDELT, Banco Mundial y USGS) en una **bandeja de temas priorizados**, **fichas de evidencia trazables** y **borradores responsables** para editores y periodistas de TVN Media.

> *La innovación no consiste en producir más texto: consiste en reducir el tiempo para encontrar un tema relevante, comprobar qué evidencia existe, identificar vacíos de información y entregar un resultado 100% trazable.*

---

## 🌟 Características Principales

1. **Arquitectura de IA en Dos Niveles (System One & System Two)**:
   - **Modelos de Decisión System One (Cloudflare Clef & TypeSafe Jev)**: Modelos no generativos de 27B/9B especializados en responder esquemas de preguntas tipadas (`noul`, `choice`, `score`). Se encargan del cálculo probabilístico de los factores de atención ($R, I, U, N$), la tipificación de afirmaciones (`hecho` vs `declaracion` vs `inferencia`) y la detección de contradicciones fácticas (**T05**) con latencias de milisegundos.
   - **Modelos Generativos System Two (OpenCode & Google Gemini)**: Encargados de la redacción, síntesis y estructuración de borradores y paquetes editoriales con citas estrictas.
2. **Priorización Explicable (Puntaje de Atención 0–100)**:
   - Fórmula determinista: $P = 30R + 25I + 20U + 15N + 10E$.
   - Componentes normalizados con desglose transparente y desempate por urgencia.
   - **Independencia del estado de evidencia**: una prioridad alta con evidencia insuficiente exige investigación y no habilita publicación automática de borrador (Prueba **T08**).
3. **Conectores Intercambiables**:
   - **Decisión (System One)**: `cloudflare` (`@cf/cloudflare/clef`), `jev` (`jev-latest`), o `mock` (offline/determinista).
   - **Generación LLM (System Two)**: `opencode` (`muse-spark-1.3-contributor-free`), `gemini` (`gemini-2.5-flash`), o `mock` (offline/determinista).
4. **Escudo Anti-Inyección y Trazabilidad de Citas**:
   - Principio: *"El texto de una fuente es dato, no instrucción"* (**T07**).
   - 100% de afirmaciones factuales enlazadas a IDs de evidencia válidos.
   - Abstención explícita ante consultas sin sustento en el corpus (**T06**).
5. **Toolchain Moderno con `uv`**:
   - Tiempos de instalación ultrarrápidos, resolución de dependencias bloqueada en `uv.lock`.
6. **Despliegue Continuo Automatizado**:
   - Pipeline de integración y entrega continua (CI/CD) mediante **GitHub Actions**, con soporte para contenedores en Fly.io o nubes como AWS.
7. **Gestión de Tareas con GitHub CLI (`gh`)**:
   - Backlog, milestones y las 10 pruebas de aceptación (**T01 a T10**) auditables vía `gh issue`.
8. **Espacio Notion Business**:
   - Cumplimiento de las 8 bases obligatorias de la Sección 5 del reto.

---

## 🏗️ Arquitectura del Repositorio

El proyecto implementa **Arquitectura Hexagonal (Ports & Adapters)**:

```
hackiathon-reto-tvn/
├── AGENTS.md                        # Protocolo y directrices para agentes de IA
├── docs/
│   ├── adr/                         # Architecture Decision Records (ADR-0001 a ADR-0010)
│   ├── notion_spec/                 # Especificación de las 8 bases para Notion Business
│   └── ARCHITECTURE.md              # Diagrama C4, secuencias y modelos de datos
├── src/hackiathon_reto_tvn/
│   ├── config.py                    # Configuración tipada vía pydantic-settings
│   ├── domain/                      # Entidades puras (models, scoring, safety)
│   ├── ports/                       # Interfaces abstractas (DecisionPort, LLMPort, StoragePort)
│   ├── adapters/                    # Implementaciones tecnológicas
│   │   ├── decision/                # Cloudflare Clef, TypeSafe Jev, Mock decision
│   │   ├── llm/                     # OpenCode, Gemini, Mock LLM
│   │   └── data/                    # CSV, GeoJSON loaders y manifest SHA-256
│   ├── services/                    # Orquestación y concurrencia (CopilotService)
│   ├── api/                         # FastAPI endpoints (/healthz, agenda, borrador, contradicciones)
│   ├── cli.py                       # CLI interactivo (hackiathon-tvn)
│   └── main.py                      # Punto de entrada ASGI
├── data/
│   ├── raw/                         # noticias.csv, indicadores.csv, eventos.geojson
│   ├── benchmark.jsonl              # 60 consultas de evaluación
│   └── manifest.json                # Manifiesto criptográfico con hashes SHA-256
├── scripts/                         # Automatización e ingesta periódica (periodic_ingestion.py)
├── tests/                           # Suite pytest (scoring, decision, llm, safety, T01-T10)
├── Dockerfile                       # Multi-stage optimizado con uv
├── fly.toml                         # Especificación para contenedores en nube
├── Makefile                         # Comandos de ingeniería (make check)
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
# --- Modelos de Decisión System One (Clasificación y Factores R, I, U, N) ---
# Proveedor: 'cloudflare' (default: @cf/cloudflare/clef), 'jev' (TypeSafe), o 'mock' (offline)
DECISION_PROVIDER=cloudflare
DECISION_CONCURRENCY_LIMIT=5

# Cloudflare Clef (Workers AI - 27B / 9B multimodal decision model)
CLOUDFLARE_ACCOUNT_ID=tu_account_id
CLOUDFLARE_API_TOKEN=tu_api_token
CLOUDFLARE_DECISION_MODEL=@cf/cloudflare/clef

# TypeSafe Jev (Alternativo comercial System One)
TYPESAFE_API_KEY=tu_clave_typesafe
TYPESAFE_MODEL=jev-latest

# --- Modelos Generativos LLM System Two (Redacción y Síntesis) ---
# Proveedor: 'opencode' (default), 'gemini', o 'mock' (offline)
LLM_PROVIDER=opencode

# OpenCode (Default - Modelo muse-spark-1.3-contributor-free)
OPENCODE_API_KEY=tu_clave_opencode
OPENCODE_BASE_URL=https://api.opencode.ai/v1
OPENCODE_MODEL=muse-spark-1.3-contributor-free

# Google Gemini (Alternativo)
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-2.5-flash

# --- Almacenamiento Persistente SQLite e Ingesta Periódica (Fly.io / Local) ---
SQLITE_DB_PATH=data/storage/copilot.db
INGESTION_ENABLED=true
INGESTION_INTERVAL_MINUTES=60
```

> **Resiliencia Determinista**: Si no se configuran tokens para Cloudflare o LLMs externos, el sistema activa de forma transparente el adaptador `mock` offline, garantizando el cumplimiento estricto de la prueba de contingencia **T10** ("Sin internet durante la demo").

---

## 💻 Uso del CLI y API

### Comandos del CLI
```bash
# Consultar el estado del sistema y conectores activos
uv run hackiathon-tvn status

# Calcular agenda priorizada (Top 5)
uv run hackiathon-tvn agenda --top 5

# Generar y validar manifiesto criptográfico SHA-256
uv run hackiathon-tvn manifest

# Generar borrador editorial para el caso prioritario
uv run hackiathon-tvn draft

# Ejecutar ciclo de ingesta en vivo (TVN RSS, GDELT, Banco Mundial, USGS)
uv run hackiathon-tvn ingest

# Consultar estadísticas de la base de datos SQLite y volumen persistente
uv run hackiathon-tvn db-status
```

### Levantar Servidor Local
```bash
# Iniciar servidor FastAPI en http://0.0.0.0:8080
uv run uvicorn hackiathon_reto_tvn.main:app --host 0.0.0.0 --port 8080 --reload
```
Endpoints principales:
* `GET /healthz` — Chequeo de salud para orquestadores y balanceadores.
* `GET /api/v1/system/info` — Estado del runtime, conector de decisión y proveedor LLM activo.
* `GET /api/v1/copilot/agenda?top_n=5` — Ranking de noticias priorizadas con componentes explicados.
* `POST /api/v1/copilot/generate-draft` — Generación estructurada de brief y guion con citas verificadas.
* `POST /api/v1/copilot/contradictions` — Detección automatizada de discrepancias y afirmaciones incompatibles (**T05**).
* `POST /api/v1/copilot/review` — Máquina de estados de revisión humana (`en_revision`, `aprobado_como_borrador`, etc.).
* `GET /api/v1/ingestion/status` — Estadísticas de almacenamiento SQLite y auditoría de ingesta.
* `POST /api/v1/ingestion/trigger` — Disparo manual de ciclo de ingesta en vivo.
* `GET /api/v1/ingestion/noticias?limit=20` — Consulta de noticias vivas persistidas en SQLite.

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

# Actualizar o cerrar una tarea completada
gh issue close 9
```

---

## 🚀 Despliegue Automatizado (CI/CD)

El ciclo de integración y despliegue continuo se orquesta completamente a través de **GitHub Actions**:
* **Pipeline de CI (`ci.yml`)**: Ejecuta en cada commit y Pull Request la suite completa de calidad (`make check`: ruff, formato, mypy y pytest con las 10 pruebas de aceptación).
* **Pipeline de CD (`fly-deploy.yml`)**: Construye de forma automatizada la imagen contenedor multi-stage (`Dockerfile`) y realiza el despliegue ante cambios en la rama `main` o mediante ejecución manual (`workflow_dispatch`).

### Arquitectura de Despliegue Agnóstica a la Nube
La solución está empaquetada como un contenedor Docker estándar e independiente de infraestructura. Actualmente se encuentra desplegada sobre **Fly.io**, pero gracias al diseño hexagonal y desacoplado, puede ser desplegada de manera transparente en proveedores cloud corporativos como **AWS** (mediante Amazon ECS, AWS App Runner o EKS) sin requerir modificaciones en el código fuente.

Para operaciones directas o inspección local de la infraestructura actual:
* [flyctl](https://fly.io/docs/hands-on/install-flyctl/) (para despliegue en Fly.io).

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
* [ADR-0010: Modelos de Decisión System One (Cloudflare Clef y TypeSafe Jev) para Clasificación y Scoring](docs/adr/0010-system-one-decision-models-cloudflare-clef-and-jev.md)

---

## 📝 Documentación en Notion Business

El espacio oficial de Notion Business contiene las 8 secciones obligatorias para la presentación final ante el jurado:
Consulte la guía de integración y esquemas en [`docs/notion_spec/README.md`](docs/notion_spec/README.md).
