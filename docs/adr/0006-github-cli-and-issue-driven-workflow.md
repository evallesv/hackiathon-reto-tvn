# ADR-0006: Gestión de Tareas y Pruebas T01–T10 mediante GitHub CLI (`gh`)

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El equipo requiere una gestión de tareas ágil, programática y auditable durante el desarrollo del hackathon.
La sección 5 del reto estipula contar con un plan de al menos 8 tareas y 3 decisiones justificadas registradas durante la ejecución, y la sección 9 enumera 10 casos de prueba de aceptación obligatorios (`T01` a `T10`).
El usuario especificó el requisito: *"Gestion de tareas y trabajo por medio de gh"*.

## Decisión

1. **Gestión Integral con GitHub CLI (`gh`)**:
   * Utilizar `gh issue` para crear, etiquetar, listar y cerrar requerimientos y pruebas.
2. **Plantillas de Issue Estandarizadas (`.github/ISSUE_TEMPLATE/`)**:
   * `01_feature.yml`: Para nuevas funcionalidades del copiloto y conectores.
   * `02_acceptance_test.yml`: Especializada para los 10 casos del reto (`T01`–`T10`), con campos para entrada, resultado esperado, resultado observado y evidencia.
   * `03_adr.yml`: Para registrar propuestas de decisiones de arquitectura.
3. **Script de Inicialización Automatizada (`scripts/gh_setup_tasks.py`)**:
   * Script interactivo/automatizado que utiliza `gh` para crear los Milestones del evento (Día 1, Día 2, Día 3), las etiquetas del proyecto y pre-crear los issues de las 10 pruebas T01–T10 y las 8 tareas base de la rúbrica.

## Consecuencias

### Positivas
* Cualquier agente o miembro del equipo puede sincronizar y auditar el estado del backlog directamente desde la terminal (`gh issue list`).
* Trazabilidad 1:1 entre los commits de Git, los PRs y los casos de aceptación del jurado.
