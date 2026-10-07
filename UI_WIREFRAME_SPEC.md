## 1. Project Overview

**Project Name**: De la Señal a la Decisión: Copiloto de Inteligencia Informativa con IA (hackiathon-reto-tvn)

**Purpose**: AI copilot for TVN Media (editorial news desk) with modular extension for banking sector. Transforms frozen public datasets (noticias.csv, indicadores.csv, eventos.geojson) into prioritized agenda rankings, traceable evidence case cards, and responsible draft outputs with human-in-the-loop validation.

**Core Architecture**: Clean Architecture / Hexagonal (Ports & Adapters). Domain logic has zero dependencies on frameworks.

**Type**: Backend service (FastAPI REST API + CLI). No existing frontend/UI code in the repository.

**Target Users** (from docs): Editors/journalists at TVN Media (editorial desk). For banking extension, analysts. The system is designed as an editorial intelligence copilot.

## 2. Documentation Found

**Project files in repo:**
- README.md - Comprehensive project description, quickstart, CLI/API usage, acceptance tests T01-T10
- AGENTS.md - Detailed agent rules, architecture, commands, invariants
- CLAUDE.md - References AGENTS.md
- docs/ARCHITECTURE.md - Architecture hexagonal, data flows, System One/System Two, scoring formula
- docs/adr/ (10 files): ADR-0001..ADR-0010 covering toolchain, ports/adapters, scoring, safety, deployment, workflow, Notion, data contracts, naming, System One
- docs/notion_spec/README.md - 8 required Notion pages for hackathon presentation
- data/manifest.json, data/benchmark.jsonl, data/raw/*.csv/*.geojson
- scripts/gh_setup_tasks.py
- tests/*.py (full test suite)
- pyproject.toml, Dockerfile, fly.toml, Makefile, .env.example

**Document formats searched:** .doc, .docx, .pdf, .txt - None found in repo. All requirements are in .md files (README, AGENTS, ARCHITECTURE, ADRs, notion_spec).

**Key requirement sources:** README.md (problem, features, API, CLI, tests), ARCHITECTURE.md (flows, scoring, users conceptually), notion_spec (8-page structure showing what must be delivered), ADRs (design decisions).

## 3. Requirements Extracted

**Functional Requirements (from code + docs):**
1. Ingest frozen datasets (noticias.csv, indicadores.csv, eventos.geojson) with null preservation (T01,T04)
2. Deduplicate/group news articles (T02) - single provenance for syndicated news
3. Detect recirculated news (T03) - preserve original publication date
4. Calculate attention score P = 30R + 25I + 20U + 15N + 10E (0-100) with tie-breaking
5. Classify via System One decision models (Cloudflare Clef/Jev/mock) for R,I,U,N, tipo_afirmacion, contradictions
6. Generate traceable evidence case cards (FichaCaso) with citations
7. Detect contradictions (T05) between statements
8. Generate editorial package (brief ≤250 words, copy ≤80 words, script 45-60s, ≥3 research questions) with strict citations
9. Enforce human-in-the-loop review (EN_REVISION → approval required)
10. Block draft publication if evidence insufficient despite high score (T08)
11. Explicit abstention when no corpus evidence (T06)
12. Anti-injection/sanitization of untrusted source text (T07)
13. Offline/demo mode with mock providers (T10)
14. SHA-256 manifest for reproducibility
15. REST API endpoints: /healthz, /api/v1/system/info, /api/v1/copilot/agenda, /generate-draft, /contradictions, /review, /manifest
16. CLI: status, agenda, manifest, draft

**Non-Functional Requirements:**
- Hexagonal architecture (ports/adapters) - swappable providers
- Deterministic tests, offline-capable
- 100% citation coverage for factual claims
- Null preservation (never impute 0)
- Strict type safety (Pydantic models, mypy)
- Reproducible via manifest
- Containerized (Docker + Fly.io)

**Business Rules:**
- P = 30R+25I+20U+15N+10E, ranges [0,40)=Bajo, [40,70)=Medio, [70,100]=Alto
- Tie-break: higher U, then lexicographic ID
- Evidence state independent of score
- If estado_evidencia is INSUFICIENTE, cannot publish draft (T08)
- Recirculation threshold: >3 days between pub and detection (calendar dates)
- Generated drafts start in EN_REVISION; only human review approves
- Source text treated as untrusted data (wrapped in <source_data>)
- Generated content must distinguish facts/declarations/inferences/hypotheses (T09)

## 4. User Roles / Personas

**Primary User:** Editorial journalist/editor at TVN Media (TVN Noticias desk)
- Needs to identify high-priority news items quickly
- Must verify evidence before publishing
- Needs traceable citations and clear distinction of fact vs inference
- Requires human-in-the-loop control

**Secondary User:** News analyst / editor-in-chief (reviewer)
- Reviews cases, approves/rejects drafts, requests more evidence
- Reviews contradictions between sources

**Extended User (modular):** Banking sector analyst (per project description - "modular extension for the banking sector") - though current implementation focuses on TVN editorial (Modalidad TVN_EDITORIAL, also has BorradorBancario model)

**Conceptual Persona (inferred):** TVN editor monitoring Panamanian news/events who needs an explainable agenda with evidence gaps clearly flagged.

## 5. Existing Application Structure

**Technology Stack:**
- Backend: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn
- Package Manager: uv (uv.lock)
- CLI: Click-style argparse (hackiathon-tvn)
- AI: Cloudflare Clef / TypeSafe Jev (System One), OpenCode/Gemini (System Two), Mock (offline)
- Data: pandas for CSV/processing
- Testing: pytest + pytest-asyncio
- Quality: ruff, mypy
- Deployment: Docker, Fly.io, GitHub Actions

**Code Organization (Hexagonal):**
- domain/ - Pure models (Noticia, Indicador, EventoGeoJSON, FichaCaso, BorradorEditorial/Bancario, scoring, safety)
- ports/ - Abstract interfaces (decision_port, llm_port, storage_port)
- adapters/ - Implementations (decision: cloudflare/jev/mock; llm: opencode/gemini/mock; data: loaders)
- services/ - CopilotService orchestration
- api/ - FastAPI routes (REST API)
- cli.py - CLI interface

**Frontend/UI:** NONE exists in repository. No HTML, JS, CSS, React, Vue, etc. This is purely backend API. Any UI would be a separate frontend consuming the REST API endpoints.

## 6. Available Data

### 6.1 noticias.csv (10 records)
Fields: id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_deteccion, fecha_extraccion, tema, origen, alcance_texto

Key data for UI display:
- Cards/lists: titulo, medio (publisher), tema (category), origen (rss/gdelt), fecha_publicacion, url
- Status: recirculation flag (NOT-009 is old recirculated), duplicate clusters (NOT-001 and NOT-007 similar)
- Special: NOT-010 has injection attempt (for safety context), themes include servicios_publicos, logistica_canal, economia, turismo, eventos_naturales, regulacion, general

### 6.2 indicadores.csv (14 records)
Fields: pais_iso3, indicador_id, anio, valor (nullable), unidad, fuente_url, fecha_extraccion, licencia

UI possibilities: KPI cards, country comparison tables, time series charts. Countries: PAN, CRI, COL, DOM, MEX, GTM. Indicators include GDP growth (NY.GDP.MKTP.KD.ZG), inflation (FP.CPI.TOTL.ZG), unemployment (SL.UEM.TOTL.ZS), population, internet, exports. Note valor can be null (e.g., PAN 2024 GDP).

### 6.3 eventos.geojson (3 features)
USGS earthquakes, Panama region. Fields: id, mag (magnitude), time (ms), updated, lon/lat/depth, place, status, url

UI: Map with markers, event cards, magnitude, location, timestamps (convert ms to datetime). magnitudes >= 3.4.

### 6.4 benchmark.jsonl (10 entries)
Evaluation queries - reference for test scenarios.

### 6.5 manifest.json
Metadata, SHA-256 hashes, counts, licenses - for "Data provenance" view.

**Data realistically displayable:** News lists/cards with clustering, priority scores, evidence state; Economic KPIs/charts by country/time; Map of seismic events; Case/Ficha cards with components, citations, draft content.

## 7. Required Screens

Based solely on project requirements (API + domain models + hackathon use case: editorial copilot for TVN):

### Screen 1: Dashboard / Home (Priority Agenda)
- **Purpose**: Main entry point showing prioritized news agenda
- **Primary user**: TVN editor/journalist
- **Main goal**: Quickly identify highest-priority stories needing attention
- **Info displayed**: Ranked list of FichaCaso (top N), score (0-100), rango (bajo/medio/alto), estado_evidencia, fuentes count, lead afirmacion/title, componentes breakdown (R,I,U,N,E), recirculation indicator
- **Inputs/filters**: Top N selector (1-20), filter by tema, filter by rango, filter by estado_evidencia, search by title/ID
- **Actions**: View case detail, Generate draft, Mark for review
- **Navigation**: To Case Detail, News Detail, Indicators, Map
- **Data**: GET /api/v1/copilot/agenda
- **States**: loading, empty (no cases), error

### Screen 2: Case Detail (FichaCaso)
- **Purpose**: Detailed view of a case with evidence, scoring, and draft management
- **Primary user**: Editor/reviewer
- **Main goal**: Review evidence sufficiency, understand scoring, manage editorial workflow
- **Info displayed**: id_caso, modalidad, puntaje + components (R,I,U,N,E with values), estado_evidencia, estado_revision, afirmaciones (with tipo, citas), fuentes (ids + details), borrador (if exists), observaciones_revision, persona_revisora, timestamps
- **Inputs**: Review update (nuevo_estado, persona_revisora, observaciones)
- **Actions**: Generate draft, Update review status (EN_REVISION/APROBADO_COMO_BORRADOR/REQUIERE_EVIDENCIA/DESCARTADO), Check contradictions
- **Navigation**: Back to Dashboard, To News Sources, To Draft Preview
- **Data**: FichaCaso from agenda, POST /generate-draft, POST /review
- **States**: loading, draft-generating, error (e.g. insufficient evidence), success

### Screen 3: Editorial Draft Preview
- **Purpose**: View generated editorial package (brief, script, copy, questions)
- **Primary user**: Editor
- **Main goal**: Review AI-generated content before human approval
- **Info displayed**: titulo_propuesto, brief_250, enfoque_interes_publico, preguntas_investigacion (≥3), fuentes_pendientes, guion_45_60s (45-60s), copy_digital_80, afirmaciones with citations, basado_unicamente_en_titular_metadatos
- **Actions**: Approve (move to approved), Request changes (requiere_evidencia), Discard
- **Navigation**: Back to Case Detail
- **Data**: BorradorEditorial from generate-draft
- **States**: loading, empty (not generated), error (citation < 100% if strict)

### Screen 4: News Sources / Cluster View
- **Purpose**: Show grouped news articles (provenance) for a case/cluster
- **Primary user**: Journalist verifying sources
- **Main goal**: See all sources in cluster, detect duplicates/recirculation
- **Info displayed**: Cluster members (noticias), medio, origen, urls, fechas (pub/detect/extract), recirculated flag, cluster key
- **Actions**: Open original URL
- **Navigation**: Back to Case/News
- **Data**: noticias from corpus (grouped)
- **States**: loading, empty

### Screen 5: Contradictions Checker
- **Purpose**: Compare two statements to detect factual contradictions (T05)
- **Primary user**: Editor verifying conflicting reports
- **Main goal**: Identify incompatible claims without arbitrarily choosing
- **Info displayed**: texto_a, texto_b, discrepancia_detectada (bool), probabilidad_discrepancia, estado, accion (must say "no seleccionar una cifra arbitrariamente"), versiones
- **Inputs**: Two text fields (texto_a, texto_b)
- **Actions**: Run check
- **Navigation**: From Case Detail or standalone
- **Data**: POST /api/v1/copilot/contradictions
- **States**: loading, result, error

### Screen 6: Economic Indicators
- **Purpose**: View World Bank indicators for regional context (PAN, CRI, COL, DOM, MEX, GTM)
- **Primary user**: Editor needing economic context
- **Main goal**: Explore macro indicators to contextualize news
- **Info displayed**: KPIs by country/indicator/year, tables, charts (time series), null values shown explicitly (no zero-fill), unidad, fuente_url
- **Inputs/filters**: Country (multi), indicador_id, year range
- **Actions**: View details
- **Navigation**: From Dashboard or global nav
- **Data**: indicadores.csv (loaded via API or direct; not exposed as dedicated endpoint but available via data model - could be added; currently loaded by service)
- **States**: loading, empty

### Screen 7: Events Map / Seismic Events
- **Purpose**: Display USGS seismic events on map (Panama region)
- **Primary user**: Editor covering natural events
- **Main goal**: Visualize event locations with details
- **Info displayed**: Map with markers, magnitude, place, time, depth, url, status
- **Actions**: Click marker for details, open USGS link
- **Navigation**: From Dashboard (eventos_naturales theme) or global nav
- **Data**: eventos.geojson
- **States**: loading, empty

### Screen 8: System Status / Info
- **Purpose**: Show runtime config (providers, models, env) - useful for demo/debug
- **Primary user**: Dev/team/demo operator
- **Info displayed**: environment, llm_provider/model, decision_provider/model, raw_data_dir, health
- **Data**: GET /api/v1/system/info, GET /healthz

## 8. User Flows

1. **Review Prioritized Agenda (Core)**
   Dashboard → View top cases by score → Select case → Case Detail → (optional) View sources/cluster → Generate draft → Draft Preview → Review/Approve/Request changes

2. **Verify Conflicting Sources**
   Case Detail (see conflicting info) → Contradictions Checker → Enter/comparison → See discrepancy result with guidance "no seleccionar arbitrariamente" → Return to case

3. **Investigate Evidence Gap (T08 scenario)**
   Dashboard shows case with high score but estado_evidencia=INSUFICIENTE → Case Detail shows components + evidence state + blocked draft generation (error) → Review fuentes_pendientes → Mark as REQUIERE_EVIDENCIA

4. **Cover Natural Event**
   Dashboard filtered by tema=eventos_naturales → Open case → Link to Events Map / view related seismic event details

5. **Economic Contextualization**
   News about economy/logistics → Case Detail → Navigate to Economic Indicators → Filter PAN/related countries/indicators

6. **Human Review Workflow**
   Case in EN_REVISION → Reviewer opens Case Detail → Reviews draft/citations → Updates review (APROBADO_COMO_BORRADOR or REQUIERE_EVIDENCIA or DESCARTADO) with observaciones/persona_revisora

## 9. UI Components

| Component | Category | Why Required |
|---|---|---|
| App Header/Top Nav | Navigation | Global navigation between Dashboard, Indicators, Events Map, Contradictions, Status |
| Sidebar (optional) | Navigation | Clear IA, persistent nav for editors |
| Priority Card | Dashboard | Shows FichaCaso summary: score, rango, evidence state, lead title, sources count |
| Score Badge (Rango) | Status | Visual indicator: Bajo/Medio/Alto with color |
| Evidence Badge | Status | INSUFICIENTE/PARCIAL/SUFICIENTE_PARA_BORRADOR |
| Review Status Badge | Status | NUEVO/EN_REVISION/REQUIERE_EVIDENCIA/APROBADO_COMO_BORRADOR/DESCARTADO |
| Score Breakdown | Data Viz | Transparent R,I,U,N,E components + formula P=30R+25I+20U+15N+10E (explainability) |
| Case Card (Detail) | Detail | Full FichaCaso view with all sections |
| Afirmacion Card | Evidence | Shows tipo (hecho/declaracion/inferencia/hipotesis), citas with id_fuente/campo/texto/url |
| Citation List | Evidence | Traceable citations (100% coverage requirement) |
| Draft Viewer | Editorial | Display brief/copy/script/questions with word/length constraints |
| News Cluster List | List | Grouped articles with recirculation flags, provenance |
| Recirculation Badge | Status | Indicates old pub vs recent detection (T03) |
| News Card | List | Individual noticia with medio/origen/fechas/tema/url |
| Contradiction Form | Form | Two inputs + result with probability, action guidance |
| KPI Card | Indicators | Single indicator value with unit, country, year, null handling |
| Indicators Table | Table | Multi-country comparison |
| Line/Bar Chart | Charts | Time series for indicators by year |
| Map (Leaflet/Mapbox) | Map | GeoJSON events with magnitude markers |
| Event Marker Popup | Map | Event details (mag, place, time, depth, link) |
| Filter Bar | Filters | Top N, tema, rango, estado_evidencia, country/indicator |
| Search Input | Filters | Find cases by title/ID |
| Empty State | UX | No data, no results |
| Loading Spinner/Skeleton | UX | Async operations (LLM/generation, decision calls) |
| Error Alert | UX | Validation errors (e.g. citation coverage, insufficient evidence) |
| Toast/Notification | UX | Success/failure actions |

## 10. Data Visualization Requirements

**Charts (Indicators):**
- Line charts: Indicator values over time (anio) per pais_iso3 (e.g., GDP growth trend)
- Bar charts: Cross-country comparison for specific year
- KPI cards: Single values (with explicit null display, not 0)
- Must show unidad and fuente_url; preserve nulls

**Tables:**
- Agenda table (sortable by score/U/ID), dense view alternative to cards
- Indicators table with all fields, nulls visible
- News cluster table with provenance

**Maps:**
- Events map (GeoJSON) centered on Panama region [5,12], [-86,-76]. Markers sized by magnitude, colored by magnitude range, click for details. Show count.

**Timelines:**
- Case timeline (creation, review states, timestamps)
- News timeline by fecha_publicacion

**Priority Visualization:**
- Score gauge/ring (0-100), color-coded by rango (bajo <40, medio 40-70, alto >=70)
- Component bars for R,I,U,N,E (normalized 0-1)

## 11. Information Architecture

**Primary IA (Top Level):**
1. Dashboard (Agenda Priorizada) - default
2. Indicadores Económicos
3. Eventos (Mapa Sísmico)
4. Verificador de Contradicciones
5. Estado del Sistema

**Detail Levels:**
- Dashboard → Case Detail → Draft Preview, Sources/Cluster
- Case Detail → Contradictions (contextual)
- Global → System Info

**Navigation:** Persistent top nav or sidebar, breadcrumbs on detail views, back actions. Clear hierarchy: Priority first (agenda), then context (indicators/events), then tools (contradictions).

**Content Priority (Visual Hierarchy):** Score + rango + evidence state > Case title/lead afirmacion > Components > Sources > Draft content. Evidence gaps (INSUFICIENTE) must be visually prominent (T08). Recirculation warnings prominent (T03).

## 12. GEMINI WIREFRAME SPECIFICATION

Copy this section directly to Gemini.

### Product
"De la Señal a la Decisión" - AI copilot for TVN Media editorial desk. Transforms frozen news/indicators/events into explainable prioritized agenda with traceable evidence and responsible editorial drafts.

### Problem
Editors need to quickly identify high-priority news, verify evidence sufficiency, detect contradictions, and generate traceable drafts without hallucinations. Current workflow lacks explainable scoring and evidence traceability.

### Target Users
- TVN Media editors/journalists (primary)
- Editorial reviewers (human-in-the-loop)
- Demo operators

### Design Objective
Create a clear, explainable UI that surfaces evidence state, scoring transparency (P=30R+25I+20U+15N+10E), and enforces responsible editorial workflow.

### Visual Hierarchy
1. Priority/Score (0-100 + rango + evidence state) - highest
2. Case identity (title/lead afirmacion, fuentes count)
3. Evidence sufficiency warnings (INSUFICIENTE) 
4. Components breakdown (explainability)
5. Sources/citations
6. Draft content (when generated)
7. Supporting context (indicators/events)

### Screens (all required)
- Dashboard (Priority Agenda)
- Case Detail (FichaCaso)
- Editorial Draft Preview
- News Sources/Cluster View
- Contradictions Checker
- Economic Indicators
- Events Map (Seismic)
- System Status/Info

### Screen Specifications

**Dashboard:**
- Layout: Header + filters + card grid/list of priority cases
- Sections: Top N filter, rango filter, evidence filter, tema filter, search; ranked cases
- Components: PriorityCard, ScoreBadge, EvidenceBadge, FilterBar, SearchInput
- Info: score, rango, estado_evidencia, lead title, sources count, componentes summary
- Interactions: click card → Case Detail, sort by score
- Nav: to other screens
- Data: GET /agenda

**Case Detail:**
- Layout: 2-column (left: evidence/components, right: actions/draft)
- Sections: Header (ID, score, badges), Components breakdown table/bars, Afirmaciones with citations, Fuentes, Review actions, Draft section
- Components: ScoreBadge, EvidenceBadge, ReviewBadge, AfirmacionCard, CitationList
- Actions: Generate draft, Update review status with form (persona_revisora, observaciones, nuevo_estado)
- Data: FichaCaso

**Draft Preview:**
- Sections: Title, Brief (≤250w), Focus, Research questions (≥3), Pending sources, Script (45-60s), Digital copy (≤80w), Citations
- Show "basado únicamente en titular/metadatos" if true

**News Sources/Cluster:**
- Table/list of noticias with medio, origen, fechas, recirculation badge, URL link

**Contradictions Checker:**
- Form: two textareas (texto_a, texto_b), check button, results panel showing discrepancy, probability, estado, accion guidance

**Economic Indicators:**
- Filters (country multi, indicador, year), KPI cards, table, line/bar charts; nulls shown explicitly

**Events Map:**
- Full-width map with markers, legend by magnitude, popup with details + USGS link

**System Status:**
- Show providers/models/env/health

### Main User Flows
As documented in Section 8.

### Data Visualization
KPIs, bar/line charts for indicators, map for events, score bars, tables. Preserve nulls. Show units.

### Responsive
Desktop-first (primary for editorial desk). Tablet acceptable; mobile secondary but should remain usable.

### UX Requirements
- Explainability: always show scoring components and evidence state
- Safety cues: INSUFICIENTE must be highly visible and block draft clearly
- Citations: always linked to fuente IDs
- Recirculation: explicit badge + note
- Empty/loading/error states on all async actions
- Clear hierarchy, readable text
- Consistent badges/colors

## 13. READY-TO-COPY GEMINI PROMPT

Copy this entire prompt into Gemini.

```text
You are creating low-fidelity and medium-fidelity wireframes for "De la Señal a la Decisión" (TVN Media AI Editorial Copilot). This is a BACKEND API project (FastAPI + CLI) - there is NO existing UI. Your task is to design a usable, explainable editorial dashboard based ONLY on the provided specifications.

PROJECT CONTEXT
The app ingests frozen datasets (noticias.csv, indicadores.csv, eventos.geojson) and produces prioritized agenda (FichaCaso) with explainable scoring P = 30R + 25I + 20U + 15N + 10E, evidence tracking, contradiction detection, and AI-generated editorial packages (brief ≤250w, copy ≤80w, script 45-60s, ≥3 research questions). Human-in-the-loop review is required. Evidence state is independent of score; insufficient evidence blocks draft publication.

CORE PRINCIPLES
- Design based strictly on the specification provided. Do NOT invent requirements contradicting it.
- Use ONLY real data fields from the datasets (no invented fields). Distinguish real fields from placeholders.
- Prioritize explainability: always make scoring (R,I,U,N,E), evidence state, and citation traceability visible.
- Safety-first: INSUFICIENTE evidence must be visually prominent; recirculation must be clearly flagged.
- Desktop-first layouts; consider tablet/mobile responsively.
- Wireframes only (not production code). Focus on UX, IA, flows.

TARGET USERS
- TVN Media editors/journalists (primary)
- Editorial reviewers (human-in-the-loop)
- Demo operators

REQUIRED SCREENS (8 total)
1. Dashboard (Priority Agenda) - ranked cases, filters, badges
2. Case Detail (FichaCaso) - components, afirmaciones/citas, review actions, draft section
3. Editorial Draft Preview - brief/copy/script/questions with constraints
4. News Sources/Cluster View - grouped noticias, recirculation, provenance
5. Contradictions Checker - compare two texts, show discrepancy/probability/action guidance
6. Economic Indicators - KPIs, table, charts (preserve nulls)
7. Events Map (Seismic) - GeoJSON map, Panama region, magnitude markers
8. System Status/Info - providers/models

REQUIRED ELEMENTS
- Badges: Rango (Bajo/Medio/Alto), EstadoEvidencia (insuficiente/parcial/suficiente_para_borrador), Review status
- Score breakdown showing R,I,U,N,E (0-1) and formula P=30R+25I+20U+15N+10E
- Citation lists (id_fuente, campo/pasaje, texto_sustento, url)
- Recirculation badge/indicator (T03)
- Null values displayed explicitly (not "0") for indicators
- Empty/loading/error states on all async actions

DATA (for realistic samples - use actual field names only)
Noticias: id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_deteccion, fecha_extraccion, tema, origen, alcance_texto (themes: servicios_publicos, logistica_canal, economia, turismo, eventos_naturales, regulacion, general)
Indicadores: pais_iso3, indicador_id, anio, valor(nullable), unidad, fuente_url, fecha_extraccion, licencia (PAN/CRI/COL/DOM/MEX/GTM)
Eventos (GeoJSON): id, mag, time(ms), updated, lon/lat/depth, place, status, url

DELIVERABLES
1. Information Architecture (site map)
2. User Flows (key flows including human review, evidence gap, contradictions)
3. Complete Screen List with purpose
4. Low-fidelity wireframes (all 8 screens)
5. Medium-fidelity wireframes for Dashboard + Case Detail (at minimum)
6. Navigation Structure (global nav, breadcrumbs)
7. Component Library (descriptions + usage, include badges/cards/charts/map)
8. Responsive Behavior (desktop-first, tablet/mobile notes)
9. Design Rationale (explainability, safety, citation traceability)

STYLE NOTES
- Clean, professional editorial UI (TVN Media context)
- Use clear visual hierarchy and color to signal states (especially warnings for INSUFICIENTE/recirculation)
- Make explainability obvious - don't hide scoring
- Show realistic sample data from the actual dataset structure.

Create comprehensive wireframes covering all screens and interactions. Focus on usability for time-pressured editors.
```


## 14. Missing Information / Questions

1. **Wireframe format preference**: Do you want the wireframes in a specific format (Figma, Excalidraw, Penpot, Mermaid/ASCII, or images)? The prompt above is tool-agnostic.

2. **Branding**: Any specific TVN Media brand guidelines/colors/logos to include? Not found in repo.

3. **Responsive breakpoints**: Any specific breakpoints required? Project doesn't specify.

4. **Additional data**: The "new data sources" mentioned in earlier task - if there are new files to integrate, they should inform UI. But none present.

5. **Real fichas.jsonl**: No fichas.jsonl exists yet in data/ (it's generated output). Wireframes should show structure from FichaCaso model.

6. **Banking extension**: BorradorBancario model exists - should UI support banking modality? Project states "modular extension for banking sector" - may want to note but focus on TVN editorial as primary.

All requirements derivable from repo are captured above. No UI code exists; everything is backend/API.
