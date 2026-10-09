# ADR-0016: Agenda de noticias recientes con respaldo congelado identificado

- **Estado**: Aceptado
- **Fecha**: 2026-10-08
- **Contexto**: El dashboard priorizaba únicamente `data/raw/noticias.csv`, un corpus congelado que contiene noticias históricas. La ingesta reciente ya se persiste en SQLite, pero no alimentaba la agenda editorial.

## Decisión

En los entornos que no sean de prueba, la agenda consulta primero las noticias persistidas en SQLite y utiliza los registros recientes dentro de `LIVE_AGENDA_MAX_AGE_DAYS` (90 días por defecto). Si no hay registros recientes válidos, o SQLite no está disponible, usa el corpus congelado como respaldo. Cada ficha incluye `origen_datos` (`ingesta_viva` o `snapshot_congelado`) y `fecha_actualizacion_fuente`, y el dashboard presenta esa procedencia de forma visible.

Los casos de ingesta viva reciben IDs deterministas derivados del ID de noticia, para que una reordenación de la agenda no cambie la identidad del caso. El entorno de pruebas conserva el corpus congelado y el comportamiento offline determinista. La evaluación benchmark no se modifica ni se mezcla con la ingesta viva.

## Consecuencias

- La agenda puede mostrar titulares recientes sin alterar `data/raw/` ni `data/manifest.json`.
- Si la ingesta está vacía o atrasada, el editor ve una advertencia de que está consultando el snapshot histórico.
- La frescura se determina con fecha de publicación y, si falta, fecha de detección o extracción; las fechas no interpretables no califican como recientes.
- El contenido disponible en la ficha sigue limitado al titular y metadatos almacenados por el feed. Una noticia reciente no equivale a verificación independiente ni a disponer del texto completo.
- El flujo de consultas analíticas y el benchmark continúan usando el corpus congelado; esta decisión modifica exclusivamente la agenda editorial.
