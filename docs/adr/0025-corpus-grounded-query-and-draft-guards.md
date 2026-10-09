# ADR-0025: Consultas extractivas y controles de evidencia para borradores

**Estado:** Aceptado  
**Fecha:** 2026-10-09

## Contexto

La auditoría reprodujo respuestas con un país/año diferente al solicitado, un calado fijo de 45 pies,
eventos sísmicos escogidos sin respetar ubicación o año y texto libre del LLM con una cita asignada
sin comprobar su sustento. Un borrador sin afirmaciones factuales también podía eludir el control de citas.
Las fuentes con etiquetas y comillas podían romper el bloque de datos del prompt.

## Decisión

- Las consultas de indicadores requieren un país del catálogo y como máximo un año. No se reemplaza
  un país ausente por otro. Sin año explícito se usa el último registro de esa serie/país y se muestra
  su año; un valor nulo no se sustituye por una observación anterior ni por cero.
- Las consultas de calado citan el titular que contiene la medición, su medio y fecha. Si aparecen
  cifras distintas, se muestran las versiones y la revisión pendiente; pueden referirse a fechas distintas.
- Las consultas USGS respetan el ID, los términos de ubicación y el año. Si hay varios eventos,
  se requiere acotar la consulta o pedir explícitamente el más reciente o el de mayor magnitud.
  La respuesta muestra la fecha UTC del evento. El reconocimiento de lugares sigue siendo léxico.
- La búsqueda general devuelve titulares/metadatos del corpus. Para detalles que esta ruta no puede
  confirmar, emite abstención y ofrece el titular relacionado para investigar. No publica texto libre
  del LLM con una cita asignada automáticamente. La generación estructurada de borradores permanece
  en sus casos de uso y adaptadores.
- Los borradores editoriales y bancarios deben declarar al menos una afirmación factual. El servidor
  deriva el alcance de titular/metadatos de los campos de las citas del caso y exige el rótulo correspondiente.
  El booleano emitido por el LLM no puede ampliar la evidencia disponible.
- Los datos de fuentes se escapan íntegramente como texto XML, incluidos IDs y atributos. La envoltura
  de fuentes se usa también en la priorización y no se omite mediante configuración.
- El filtro de citas conserva y compara negaciones simples. No resuelve su alcance por cláusula.

## Consecuencias y límites

Se cierran los fallos reproducidos con pruebas de regresión offline. Algunas preguntas abiertas requieren
ahora una abstención o una consulta más precisa. Las coincidencias léxicas, IDs y pasajes no demuestran
implicación semántica ni extraen todos los hechos de la prosa libre. La revisión humana de afirmaciones
y del borrador completo sigue pendiente como medición independiente de sustento (sección 9.1).

Los controles reducen superficies concretas de inyección; no acreditan resistencia universal. La suite
automatizada tampoco demuestra por sí sola uso sustantivo de NLP/ML ni desempeño de proveedores remotos.

## Verificación

`make check`: 177 pruebas aprobadas, Ruff/formato y mypy correctos al integrar esta decisión.
Las regresiones cubren país/año, calado, identidad/ubicación de sismos, omisión de afirmaciones,
rótulo de evidencia, escape de XML y adición/omisión de negaciones. El corpus congelado permanece intacto.
