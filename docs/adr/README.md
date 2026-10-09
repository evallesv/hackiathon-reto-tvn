# Registro de Decisiones de Arquitectura (ADR)

Este directorio alberga los **Architecture Decision Records (ADR)** del proyecto `hackiathon-reto-tvn`. Los ADR documentan el contexto, las alternativas evaluadas, la decisión técnica adoptada y las consecuencias para garantizar la trazabilidad y reproducibilidad del proyecto.

## Estructura de un ADR

Cada decisión sigue el formato estándar MADR (Markdown Architectural Decision Records):
* **Título**: Número secuencial y título descriptivo (`XXXX-nombre-de-la-decision.md`).
* **Estado**: `Propuesto` | `Aceptado` | `Superado` | `Rechazado`.
* **Contexto**: Qué problema se resuelve y qué restricciones existen (técnicas, de negocio o del reglamento del hackathon).
* **Decisión adoptada**: Qué solución se eligió y por qué.
* **Consecuencias**: Beneficios obtenidos y compromisos asumidos.
* **Conformidad con el Reto**: Relación directa con los criterios de evaluación, pruebas T01–T10 o la rúbrica del jurado.

## Índice de ADRs

| ID | Título | Estado | Fecha | Área |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-0001](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0001-python-uv-toolchain-and-project-layout.md) | Adopción de Python UV y Layout Estructurado `src/` | Aceptado | 2026-10-06 | Toolchain / Entorno |
| [ADR-0002](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0002-ports-and-adapters-for-llm-connectors.md) | Arquitectura Hexagonal para Conectores LLM Intercambiables (OpenCode y Gemini) | Aceptado | 2026-10-06 | IA / Conectores |
| [ADR-0003](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0003-attention-score-and-evidence-engine.md) | Motor de Puntaje de Atención Explicable e Independencia del Estado de Evidencia | Aceptado | 2026-10-06 | Dominio / Scoring |
| [ADR-0004](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0004-anti-hallucination-and-prompt-injection-defenses.md) | Escudos Anti-Inyección de Prompts y Validación Estricta de Citas | Aceptado | 2026-10-06 | Seguridad y Ética |
| [ADR-0005](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0005-fly-io-machines-deployment.md) | Despliegue en Fly.io Machines con Docker Multi-Stage y Health Checks | Aceptado | 2026-10-06 | Infraestructura / Ops |
| [ADR-0006](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0006-github-cli-and-issue-driven-workflow.md) | Gestión de Tareas y Pruebas T01–T10 mediante GitHub CLI (`gh`) | Aceptado | 2026-10-06 | Gestión y Flujo |
| [ADR-0007](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0007-notion-business-contract-and-sync.md) | Estructura de Documentación y Registro en Notion Business | Aceptado | 2026-10-06 | Documentación |
| [ADR-0008](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0008-data-contract-reproducibility-and-manifest.md) | Contrato de Datos, Ingesta No Bloqueante y Manifiesto Criptográfico SHA-256 | Aceptado | 2026-10-06 | Datos / Reproducibilidad |
| [ADR-0009](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0009-snake-case-naming-convention-for-data-contracts.md) | Convención de Nombres `snake_case` para Contratos de Datos y API | Aceptado | 2026-10-06 | Datos / API |
| [ADR-0010](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0010-system-one-decision-models-cloudflare-clef-and-jev.md) | Modelos de Decisión System One (Cloudflare Clef y TypeSafe Jev) para Clasificación y Scoring | Aceptado | 2026-10-06 | IA / Decisión System One |
| [ADR-0011](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0011-sqlite-persistent-storage-and-periodic-ingestion.md) | Almacenamiento Persistente SQLite en Fly.io Volumes e Ingesta Periódica de Fuentes Vivas | Aceptado | 2026-10-06 | Almacenamiento e Ingesta |
| [ADR-0012](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0012-multi-agent-git-workflow-and-main-protection.md) | Protocolo de Colaboración Multi-Agente, Historial Lineal y Protección de `main` | Aceptado | 2026-10-07 | Flujo de Trabajo / Git |
| [ADR-0013](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0013-unified-opencode-routing-for-system-one-and-two.md) | Unificación de Ruteo de Modelos System One y System Two mediante OpenCode API | Aceptado | 2026-10-07 | IA / Ruteo Unificado |
| [ADR-0014](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0014-baseline-evaluation-and-60-query-benchmark.md) | Evaluador de Baselines y Benchmark Formal de 60 Consultas Etiquetadas | Aceptado | 2026-10-07 | Evaluación y Benchmark |
| [ADR-0015](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0015-embedded-glassmorphism-web-dashboard.md) | Dashboard Web Interactivo Embebido (Dark Glassmorphism) para Demostración en Vivo | Aceptado | 2026-10-07 | Frontend / UX Jurado |
| [ADR-0016](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0016-resilient-snapshot-candidate-acquisition.md) | Reintentos y publicación atómica de snapshots candidatos | Aceptado | 2026-10-08 | Ingesta / Reproducibilidad |
| [ADR-0017](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0017-live-news-agenda-with-labeled-frozen-fallback.md) | Agenda con noticias recientes y respaldo congelado identificado | Aceptado | 2026-10-08 | Datos / UX editorial |
| [ADR-0018](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0018-unified-live-evidence-and-editorial-case-review.md) | Evidencia viva compartida por consultas, agenda y fichas | Aceptado | 2026-10-08 | Datos / Flujo editorial |
| [ADR-0019](file:///Users/evalle/sources/personal/hackiathon-reto-tvn/docs/adr/0019-sqlite-offline-snapshot-package.md) | Paquete de snapshot local y consultable en SQLite | Aceptado | 2026-10-09 | Datos / Reproducibilidad |
