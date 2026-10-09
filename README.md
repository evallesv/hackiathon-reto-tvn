# De la Señal a la Decisión: Copiloto de Inteligencia Informativa con IA

[![CI](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml/badge.svg)](https://github.com/evallesv/hackiathon-reto-tvn/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://docs.astral.sh/uv/)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)
[![Decision Model: Cloudflare Clef](https://img.shields.io/badge/Decision%20Model-Cloudflare%20Clef-F38020.svg)](https://developers.cloudflare.com/workers-ai/)
[![Default LLM: OpenCode](https://img.shields.io/badge/LLM-OpenCode%20muse--spark-green.svg)](https://opencode.ai)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-lightgrey.svg)](LICENSE)


Prototipo de **copiloto editorial y análisis de entorno con inteligencia artificial** diseñado para la 4ta edición del **HackIAthon** (Viamatica / ADEN / TVN Media).

La solución combina un corpus público congelado (para evaluación reproducible y consultas históricas) con ingesta viva de RSS TVN, GDELT, Banco Mundial y USGS. Esta información alimenta una **bandeja de temas priorizados**, **fichas de evidencia trazables** y **borradores responsables** para editores y periodistas de TVN Media.

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
   - El modo estricto rechaza afirmaciones factuales estructuradas con citas inexistentes o términos ausentes del pasaje (**T09**); no prueba que cada afirmación del texto libre esté citada ni su implicación semántica.
   - Abstención explícita canónica `[ABSTENCIÓN EXPLÍCITA]` ante consultas sin sustento en el corpus (**T06**).
5. **Dashboard Web Interactivo Dark Glassmorphism**:
   - Interfaz web productiva servida directamente por FastAPI en `http://localhost:8080/` o `/dashboard`.
   - Cero dependencias pesadas de npm (HTML5, Vanilla CSS Dark Glassmorphic, Javascript reactivo).
   - 4 Vistas en vivo: 1) Agenda Priorizada con desglose de fórmula $P$ y alerta T08; 2) Fichas de Evidencia con brief (250 palabras), guion (45-60s), copy digital (80 palabras), extensión bancaria y controles de revisión humana; 3) Consola Interactiva del Jurado con botones de prueba inmediata (T04, T05, T06, T07, USGS) y consulta libre; 4) Métricas exploratorias de desarrollo y verificador de integridad SHA-256.
   - La agenda y las consultas usan primero noticias recientes persistidas en SQLite (ventana retrospectiva configurable `LIVE_AGENDA_MAX_AGE_DAYS`, 90 días por defecto), además de conservar el snapshot para preguntas históricas. Indicadores y eventos vivos se combinan por sus claves con las series congeladas. Si no hay noticia reciente, la agenda identifica claramente el respaldo histórico; el entorno de pruebas sigue usando solo el snapshot.
   - `data/snapshot/snapshot.sqlite` empaqueta el corpus congelado y, cuando existe, noticias recientes, indicadores y eventos de la base local. La copia se abre en modo de solo lectura, incluye su manifiesto/hash y excluye revisiones editoriales y bitácoras de ingesta. `make sqlite-snapshot` la genera sin modificar `data/raw/` ni `data/manifest.json`.
6. **Benchmark reproducible en desarrollo**:
   - `data/benchmark.jsonl` contiene 60 consultas: 40 de desarrollo y 20 reservadas.
   - La API ejecuta el conjunto de desarrollo (40); el conjunto reservado no está aislado del repositorio y no se presenta como evaluación ciega.
   - En ejecución local offline del 2026-10-09 sobre el snapshot SQLite sellado, la recencia obtuvo P@5 **0.00 (0/5)** y la fórmula P **0.40 (2/5)**. Las etiquetas se basan en palabras clave y no son una evaluación editorial independiente; la mejora relativa queda como no disponible con baseline cero.
   - La evaluación de contradicciones compara regex con diez pares sintéticos procesados por el adaptador de decisión configurado (`mock`, Cloudflare o Jev); informa Macro-F1 y el proveedor/modelo usados. El modo `mock` es determinista y no representa desempeño de un modelo remoto. La evaluación reservada requiere custodia externa.
   - Las tasas de cita y abstención miden condiciones estructurales de respuestas seleccionadas; no verifican sustento semántico ni demuestran ausencia de alucinaciones.
7. **Extensión Modular para Sector Banca (CU-05)**:
   - Generación de boletines de entorno macroeconómico y logístico (PIB, inflación, embalses del Canal de Panamá) para comités de riesgo sectorial, preservando las series exactas del Banco Mundial (**T04**).
8. **Persistencia Transaccional SQLite WAL y Flujo Human-in-the-Loop**:
   - Almacenamiento persistente en SQLite (`fichas_casos`) para trazabilidad de estados (`EN_REVISION`, `APROBADO_COMO_BORRADOR`, `REQUIERE_EVIDENCIA`, `RECHAZADO`), persona revisora y notas editoriales; la vista de fichas une casos guardados con la agenda viva actual y restaura sus revisiones al actualizar.
   - Ingesta periódica en segundo plano de RSS, GDELT, Banco Mundial y USGS sobre volumen persistente en Fly.io (`/data/copilot.db`), estrictamente desacoplada del corpus congelado.
9. **Toolchain Moderno con `uv`**:
   - Tiempos de instalación ultrarrápidos, resolución de dependencias bloqueada en `uv.lock`.
10. **Despliegue Continuo Automatizado**:
    - Pipeline de integración y entrega continua (CI/CD) mediante **GitHub Actions** en Fly.io Machines.
11. **Espacio Notion Business (8 Páginas Oficiales)**:
    - Especificación completa de las 8 bases del reto documentadas en Markdown en `docs/notion_spec/` (incluyendo guión oficial para pitch de 10 minutos).

---

## 🏗️ Arquitectura del Repositorio

El proyecto implementa **Arquitectura Hexagonal (Ports & Adapters)**:

```
hackiathon-reto-tvn/
├── AGENTS.md                        # Protocolo y directrices para agentes de IA
├── docs/
│   ├── adr/                         # Architecture Decision Records (ADR-0001 a ADR-0013)
│   ├── notion_spec/                 # Especificación de las 8 páginas para Notion Business
│   └── ARCHITECTURE.md              # Diagrama C4, secuencias y modelos de datos
├── src/hackiathon_reto_tvn/
│   ├── config.py                    # Configuración tipada vía pydantic-settings
│   ├── domain/                      # Entidades puras (models, scoring, safety)
│   ├── ports/                       # Interfaces abstractas (DecisionPort, LLMPort, StoragePort)
│   ├── adapters/                    # Implementaciones tecnológicas
│   │   ├── decision/                # Cloudflare Clef, TypeSafe Jev, Mock decision
│   │   ├── llm/                     # OpenCode, Gemini, Mock LLM
│   │   └── data/                    # Loaders congelados, Live fetchers y SQLite storage
│   ├── services/                    # Orquestación (CopilotService, BaselineEvaluator, IngestionScheduler)
│   ├── api/                         # FastAPI REST API (/healthz, agenda, query, fichas, borrador, ingesta)
│   ├── ui/                          # Dashboard Web (index.html, styles.css, app.js - Dark Glassmorphism)
│   └── main.py                      # Punto de entrada ASGI con lifespan worker, rutas estáticas y server
├── data/
│   ├── raw/                         # noticias.csv, indicadores.csv, eventos.geojson (congelado)
│   ├── snapshot/                    # snapshot.sqlite y manifiesto del paquete offline de consulta
│   ├── benchmark.jsonl              # 60 consultas etiquetadas de evaluación (40 dev / 20 jurado)
│   ├── benchmark_results.json       # Resultados cacheados del benchmark y comparación de baselines
│   ├── fichas.jsonl                 # 5 fichas canónicas iniciales (incluye caso de alerta T08)
│   └── manifest.json                # Manifiesto criptográfico con hashes SHA-256
├── scripts/                         # Automatización (periodic_ingestion.py, run_benchmark.py)
├── tests/                           # Suite pytest (scoring, decision, llm, safety, storage, ui, T01-T10)
├── Dockerfile                       # Multi-stage optimizado con uv y volumen /data
├── fly.toml                         # Especificación para contenedores y volumen sentria_data
├── Makefile                         # Comandos de ingeniería (make check, make benchmark, make manifest)
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

## 🌐 Interfaz API REST y Ejecución del Servidor

El copiloto opera como un **Backend API REST de alto rendimiento**, diseñado para alimentar interfaces web editoriales, dashboards y aplicaciones frontend.

### 1. Iniciar Servidor Backend
```bash
# Iniciar servidor backend FastAPI en http://0.0.0.0:8080
uv run uvicorn hackiathon_reto_tvn.main:app --host 0.0.0.0 --port 8080 --reload

# O mediante el comando empaquetado
uv run hackiathon-server
```

### 2. Documentación Interactiva (Swagger / OpenAPI)
Una vez iniciado el servidor, accede a la documentación interactiva y explorador de API:
* **Swagger UI**: `http://localhost:8080/docs`
* **Redoc**: `http://localhost:8080/redoc`
* **OpenAPI JSON**: `http://localhost:8080/openapi.json`

### 3. Endpoints Principales del Backend
* `GET /` o `/dashboard` — **Dashboard Web Interactivo Dark Glassmorphism** con las 4 vistas en vivo.
* `GET /healthz` — Chequeo de salud para orquestadores y balanceadores (Fly.io).
* `GET /api/v1/system/info` — Estado del runtime, conector de decisión y proveedor LLM activo.
* `GET /api/v1/copilot/agenda?top_n=5` — Ranking de noticias priorizadas con desglose explicable de $P$.
* `POST /api/v1/copilot/query` — **Motor de consulta en lenguaje natural** con citas verificadas y abstención explícita (**T04, T06, T07**).
* `GET /api/v1/copilot/fichas` — Casos persistidos más las fichas de la agenda viva actual, con evidencias y borradores.
* `GET /api/v1/copilot/fichas/{id_caso}` — Detalle estructurado de una ficha de evidencia específica.
* `GET /api/v1/copilot/fichas/export` — Exportación de casos persistidos y agenda viva actual en formato JSON para auditoría.
* `POST /api/v1/copilot/generate-draft` — Generación estructurada de brief y guion TV con citas verificadas (**T09**).
* `POST /api/v1/copilot/generate-banking-draft` — Generación de **boletín bancario macroeconómico y logístico** (**CU-05**).
* `POST /api/v1/copilot/contradictions` — Detección automatizada de discrepancias y afirmaciones incompatibles (**T05**).
* `POST /api/v1/copilot/review` — Máquina de estados y persistencia en SQLite de la **revisión humana** (`en_revision`, `aprobado_como_borrador`, etc.).
* `GET /api/v1/copilot/benchmark/metrics` — Métricas del conjunto de desarrollo (40 consultas) y comparativa exploratoria frente a baselines.
* `GET /api/v1/copilot/manifest` — Consulta del manifiesto criptográfico SHA-256.
* `GET /api/v1/ingestion/status` — Estadísticas de almacenamiento SQLite y auditoría de ingesta en vivo.
* `POST /api/v1/ingestion/trigger` — Disparo manual de ciclo de ingesta en vivo.
* `GET /api/v1/ingestion/noticias?limit=20` — Consulta de noticias vivas persistidas en SQLite.

### 4. Scripts y Comandos de Utilidad
```bash
# Iniciar el servidor local (Dashboard en http://localhost:8080/)
uv run hackiathon-server

# Ejecutar el benchmark de desarrollo (40 consultas); el conjunto reservado queda deshabilitado
make benchmark

# Crear el paquete SQLite offline desde el corpus y la ingesta local disponible
make sqlite-snapshot

# Generar o verificar manifiesto criptográfico SHA-256
make manifest

# Ejecutar ciclo de ingesta continua en segundo plano
uv run python scripts/periodic_ingestion.py --continuous --interval 60

# Ejecutar la verificación completa de calidad (Ruff, Format, Mypy, 134 tests Pytest)
make check

# Auditar sin escribir un snapshot candidato (cambia la ruta con SNAPSHOT_DIR)
make audit-snapshot SNAPSHOT_DIR=/private/tmp/snapshot-candidate

# Descargar y preparar un candidato. Se publica solo si supera todos los mínimos;
# si queda incompleto, conserva únicamente un informe .audit-report.json.
make prepare-snapshot CANDIDATE_DIR=/private/tmp/snapshot-candidate-2026-10
```

---

## 🧪 Pruebas de Aceptación (T01 a T10)

El proyecto cuenta con cobertura automatizada para las **10 pruebas obligatorias de la Sección 9** y un total de **134 tests en la suite**:

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

El ciclo de integración y despliegue continuo se orquesta exclusivamente a través de **GitHub Actions**:
* **Pipeline de CI (`ci.yml`)**: Ejecuta en cada commit y Pull Request la suite completa de calidad (`make check`: ruff, formato, mypy y pytest).
* **Pipeline de CD (`fly-deploy.yml`)**: Construye de forma automatizada la imagen contenedor multi-stage (`Dockerfile`) y realiza el despliegue ante cambios en la rama `main` o mediante ejecución manual con GitHub CLI (`gh workflow run fly-deploy.yml`).

### Arquitectura de Despliegue Agnóstica a la Nube
La solución está empaquetada como un contenedor Docker estándar e independiente de infraestructura. Actualmente se encuentra conectada para entrega continua sobre **Fly.io**, pero gracias al diseño hexagonal y desacoplado, puede ser desplegada de manera transparente en proveedores cloud corporativos como **AWS** (mediante Amazon ECS, AWS App Runner o EKS) sin requerir modificaciones en el código fuente.

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
* [ADR-0011: Almacenamiento Persistente SQLite en Fly.io Volumes e Ingesta Periódica de Fuentes Vivas](docs/adr/0011-sqlite-persistent-storage-and-periodic-ingestion.md)
* [ADR-0012: Flujo Git para Desarrollo Multi-Agente, Estandarización en AGENTS.md y Protección de Main](docs/adr/0012-multi-agent-git-workflow-and-main-protection.md)
* [ADR-0013: Ruteo Unificado OpenCode para Modelos de Decisión System One y Generativos System Two](docs/adr/0013-unified-opencode-routing-for-system-one-and-two.md)
* [ADR-0014: Evaluación de Baselines y Benchmark Formal de 60 Consultas](docs/adr/0014-baseline-evaluation-and-60-query-benchmark.md)
* [ADR-0024: Protección del benchmark reservado y reporte del adaptador real](docs/adr/0024-protect-reserved-benchmark-and-report-real-adapter.md)
* [ADR-0015: Dashboard Web Interactivo Embebido para Demostración al Jurado](docs/adr/0015-embedded-glassmorphism-web-dashboard.md)
* [ADR-0016: Reintentos y Publicación Atómica de Snapshots Candidatos](docs/adr/0016-resilient-snapshot-candidate-acquisition.md)

---

## 🌿 Flujo Git y Desarrollo Colaborativo Multi-Agente

Para garantizar la estabilidad del servicio en producción (Fly.io) y facilitar el trabajo concurrente entre múltiples desarrolladores y agentes de IA:

1. **Protección de Producción (`main`)**: La rama `main` despliega automáticamente a producción. **Está terminantemente prohibido hacer commits o pushes directos a `main`**.
2. **Ciclo de Trabajo con Ramas**:
   ```bash
   git fetch origin
   git checkout -b feat/<nombre-tarea> origin/main
   # Desarrollar y verificar con make check
   git add <archivos>
   git commit -m "feat(alcance): descripción clara"
   # Mantener historial lineal y limpio antes de subir
   git fetch origin && git rebase origin/main
   git push -u origin feat/<nombre-tarea>
   gh pr create --fill
   ```
3. **Validación Previa (`make check`)**: Todo cambio debe pasar el gate completo (`ruff`, `mypy` y pytest) antes de solicitar revisión.
4. **Protección Local de Git**: Configure el hook pre-push ejecutando `make setup-hooks` para bloquear pushes accidentales a `main`.

---

## 📝 Documentación en Notion Business

El espacio oficial de Notion Business contiene las **8 páginas obligatorias** de la Sección 5 del reto, completamente redactadas y disponibles en [`docs/notion_spec/`](docs/notion_spec/):

| # | Página / Documento | Contenido y Alcance | Archivo Markdown |
| :-: | :--- | :--- | :--- |
| **01** | **Inicio del reto** | Equipo Sentria, problema editorial TVN, usuarios, alcance y accesos. | [`01-inicio-del-reto.md`](docs/notion_spec/01-inicio-del-reto.md) |
| **02** | **Plan y decisiones** | Backlog de 10 tareas, cronograma y 5 decisiones de arquitectura (ADRs). | [`02-plan-y-decisiones.md`](docs/notion_spec/02-plan-y-decisiones.md) |
| **03** | **Catálogo de datos** | 4 fuentes, licencias (CC BY 4.0, TVN, USGS), nulos y hashes SHA-256. | [`03-catalogo-de-datos.md`](docs/notion_spec/03-catalogo-de-datos.md) |
| **04** | **Diseño de solución** | Arquitectura Hexagonal, Pydantic, fórmula $P$, prompts seguros y límites. | [`04-diseno-de-solucion.md`](docs/notion_spec/04-diseno-de-solucion.md) |
| **05** | **Casos y evidencias** | 5 fichas canónicas; IDs y fragmentos pasan controles léxicos, con revisión humana para sustento semántico. | [`05-casos-y-evidencias.md`](docs/notion_spec/05-casos-y-evidencias.md) |
| **06** | **Pruebas y métricas** | Matriz T01-T10 y benchmark en desarrollo; resultados exploratorios y límites documentados. | [`06-pruebas-y-metricas.md`](docs/notion_spec/06-pruebas-y-metricas.md) |
| **07** | **Riesgos y ética** | Matriz de riesgos, derechos de autor, anti-inyección y reserva humana. | [`07-riesgos-y-etica.md`](docs/notion_spec/07-riesgos-y-etica.md) |
| **08** | **Presentación al jurado** | Pitch cronometrado de 10 minutos, guión para el expositor y respuestas clave. | [`08-presentacion-al-jurado.md`](docs/notion_spec/08-presentacion-al-jurado.md) |
