# Estructura Obligatoria de Notion Business (Sección 5 del Reto)

Notion es el **espacio central de trabajo y la superficie oficial de presentación** ante el jurado.
Este directorio documenta el contenido exacto y los esquemas de las **8 páginas o bases de datos exigidas** por las bases de la 4ta edición del hackIAthon.

## Índice de Páginas Obligatorias

| # | Página / Base en Notion | Contenido Exigido | Estado |
| :--- | :--- | :--- | :--- |
| **01** | **Inicio del reto** | Equipo, modalidad (Editorial TVN), problema, usuario, alcance, criterios de éxito, accesos a demo y repo. | Configurado |
| **02** | **Plan y decisiones** | Backlog (mínimo 8 tareas), responsables, estados, cronología y al menos 3 decisiones técnicas justificadas (ADRs). | Sincronizado vía `gh` y `docs/adr/` |
| **03** | **Catálogo de datos** | Fuentes (TVN RSS, GDELT, Banco Mundial, USGS), URLs, cobertura, licencias, transformaciones y SHA-256 del snapshot. | Generado en `data/manifest.json` |
| **04** | **Diseño de solución** | Arquitectura Hexagonal, modelo de datos Pydantic, fórmula de atención $P$, prompts de OpenCode y Gemini, límites del sistema. | Documentado en `docs/ARCHITECTURE.md` |
| **05** | **Casos y evidencias** | Al menos 5 fichas trazables con IDs, fuentes, puntaje desglosado, estado de evidencia (incluyendo 1 caso con evidencia insuficiente), borrador y revisor. | Serializado en `data/fichas.jsonl` |
| **06** | **Pruebas y métricas** | Matriz de las 10 pruebas obligatorias (T01 a T10), resultado esperado vs observado, evidencia y corrección. | Cubierto por `tests/test_acceptance_t01_t10.py` |
| **07** | **Riesgos y ética** | Privacidad, derechos de autor por fuente, sesgos, mitigación de prompt injection y escenarios fuera de alcance. | Verificado en `src/hackiathon_reto_tvn/domain/safety.py` |
| **08** | **Presentación al jurado** | Pitch oficial navegable de 10 minutos: Problema → Solución → Demo → IA y evidencias → Resultados → Límites → Próximos pasos. | Esquematizado para presentación en vivo |
