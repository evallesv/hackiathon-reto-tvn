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
| [ADR-0009](0009-snake-case-naming-convention-for-data-contracts.md) | Convención de Nombres `snake_case` para Contratos de Datos y API | Aceptado | 2026-10-06 | Datos / API |
