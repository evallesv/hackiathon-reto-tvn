# ADR-0007: Estructura de Documentación y Registro en Notion Business

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

La sección 5 del documento del reto declara a **Notion Business como requisito indispensable y superficie oficial de presentación**.
La estructura obligatoria por equipo exige las siguientes 8 páginas o bases de datos:
1. **Inicio del reto**: Equipo, modalidad, problema, usuario, alcance, criterios de éxito y accesos a demo y repositorio.
2. **Plan y decisiones**: Backlog, responsables, estados, cronología y decisiones técnicas o de producto (al menos 8 tareas y 3 decisiones justificadas).
3. **Catálogo de datos**: Fuente, URL, fecha de extracción, cobertura, campos, licencia/condiciones, transformaciones y hash del snapshot.
4. **Diseño de solución**: Arquitectura, modelo de datos, reglas, modelos, prompts, versiones y límites del sistema.
5. **Casos y evidencias**: Fichas con IDs, fuentes, puntaje desglosado, estado de evidencia, borrador y persona revisora (mínimo 5 fichas trazables, incluyendo 1 caso sin evidencia suficiente).
6. **Pruebas y métricas**: Matriz con los 10 casos de prueba de la sección 9 (T01–T10) y métricas de la ejecución final.
7. **Riesgos y ética**: Privacidad, derechos, sesgos, ataques al agente, controles y escenarios fuera de alcance.
8. **Presentación al jurado**: Flujo de pitch de 10 minutos navegable desde Notion.

## Decisión

1. Mantener un espejo en Markdown en el repositorio (en `docs/notion_spec/`) con los esquemas de las 8 bases para que puedan exportarse o sincronizarse a Notion vía API o carga por lote.
2. Formato de exportación interoperable en JSON (`fichas.jsonl` y `manifest.json`) que mapea exactamente con las columnas y propiedades requeridas en las bases de datos de Notion.
3. El código del copiloto incluye endpoints y métodos de exportación para formatear las fichas con Markdown enriquecido apto para bloques de Notion.

## Consecuencias

### Positivas
* Asegura el cumplimiento previo de habilitación ante el jurado.
* Elimina discrepancias entre el código del repositorio y lo exhibido en la presentación final.
