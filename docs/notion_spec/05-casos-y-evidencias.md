# 05 — Cinco Ejemplos Locales y Evidencias para Revisar

> Contenido local preparado. Publicación en Notion, revisión humana y exportación final de fichas pendientes.

## 1. Naturaleza de estos ejemplos

Los IDs `CASO-001` a `CASO-005` aparecen en [fichas.jsonl](../../data/fichas.jsonl) como **fixtures ilustrativos**. Sus puntajes son valores de esos fixtures, no el ranking actual ni una decisión de personas reales. Los nombres, aprobaciones y detalles de los borradores del archivo no acreditan revisión humana ni sustento; no se presentan aquí como resultados validados.

Esta página conserva cinco recorridos de comprobación con registros que existen en [noticias.csv](../../data/raw/noticias.csv) e [indicadores.csv](../../data/raw/indicadores.csv). «Existe en el corpus local» no significa que la noticia, el enlace externo o una cifra histórica hayan sido verificados de nuevo con su emisor. Las fuentes se revisan en el ensayo y se identifican mediante el manifiesto utilizado.

| Ejemplo local | IDs verificables en el corpus | P del fixture | Qué se comprueba |
| :--- | :--- | :--- | :--- |
| `CASO-001` | `NOT-001`, `NOT-007` | 80.0 | Titulares relacionados y atribución; repetición no acredita corroboración independiente. |
| `CASO-002` | `NOT-002`, `NOT-003` | 84.25 | Tránsitos y calado son contenidos distintos; recuperar el titular pertinente sin inventar detalles. |
| `CASO-003` | `NOT-009` | 47.5 | Separar publicación histórica y detección posterior. |
| `CASO-004` | `PAN-NY.GDP.MKTP.KD.ZG-2023`, `PAN-FP.CPI.TOTL.ZG-2023` | 73.75 | Citar por separado PIB e inflación, preservando país, año y unidad. |
| `CASO-005` | `NOT-010` | 83.75 | Fuente adversarial sintética y guardrail sobre una ficha con evidencia insuficiente. |

Para las fichas actuales, abrir el [servicio](../../src/hackiathon_reto_tvn/services/copilot_service.py) mediante `GET /api/v1/copilot/fichas` y exportar `GET /api/v1/copilot/fichas/export`. Registrar ID, fuentes, P y componentes, estado de evidencia, borrador y revisión de esa ejecución. El ID de un fixture histórico puede no corresponder al mismo tema o estado en la agenda generada.

## 2. Ejemplos trazables

### `CASO-001` — Titulares MOP y verificación pendiente

* **Registro local:** `NOT-001`, campo `titulo`: «MOP anuncia plan de rehabilitación de vías en la Ciudad de Panamá». Medio registrado: TVN Noticias. Publicación registrada: `2024-03-10T14:30:00Z`. Alcance: `titular_metadatos`.
* **Registro relacionado:** `NOT-007`, campo `titulo`: «MOP anuncia plan de rehabilitación de vías principales». No se acredita por esos dos titulares una fuente primaria ni corroboración independiente.
* **Componentes del fixture:** R=0.85, I=0.80, U=0.75, N=0.70, E=0.90; producen P=80.0. La E y el estado del fixture son ilustrativos; consultar los componentes y evidencia calculados por el servicio en el ensayo.
* **Atribución permitida del ejemplo:** el titular local de TVN informa ese anuncio, **basado únicamente en titular/metadatos**. No se derivan cronograma, presupuesto, demanda de transportistas, inicio de obras ni horarios nocturnos.
* **Preguntas pendientes:** ¿qué documento primario respalda el anuncio?, ¿cuál es el alcance y cronograma confirmado?, ¿qué presupuesto y responsable constan en esa fuente?
* **Borrador y revisión:** no se acredita aquí un borrador validado. Generarlo desde el caso resuelto por el servidor cuando corresponda, revisar todas sus afirmaciones y registrar una persona real en Notion.

### `CASO-002` — Calado y tránsitos sin mezclar evidencia

* **Registro del calado:** `NOT-003`, campo `titulo`: «ACP reporta aumento de calado a 45 pies ante mejora en embalses». Medio registrado: Panamá América. Publicación registrada: `2024-03-11T11:15:00Z`. Alcance: `titular_metadatos`.
* **Otro registro:** `NOT-002` dice «Canal de Panamá proyecta normalización gradual de tránsitos diarios tras lluvias». No aporta por sí mismo la cifra de calado ni confirma que ambas piezas sean un mismo evento.
* **Componentes del fixture:** R=0.95, I=0.90, U=0.70, N=0.65, E=0.95; P=84.25, ilustrativo.
* **Atribución permitida:** el titular `NOT-003` reporta 45 pies, **basado únicamente en titular/metadatos**. No acredita nombres de lagos, capacidad adicional, ingresos del Estado o declaraciones que no aparecen en ese registro.
* **Agrupación:** los registros `NOT-102` y `NOT-103` de pruebas sintéticas no están en `noticias.csv`; no se cuentan aquí como fuentes reales del caso. La prueba T02 conserva sus propios IDs sintéticos y evalúa agrupación léxica.
* **Verificación pendiente:** recuperar fuente primaria y fecha de vigencia; distinguir calado de tránsitos; ante mediciones distintas, presentar versiones sin escoger arbitrariamente. Exportar el borrador y revisión reales del ensayo.

### `CASO-003` — Fecha original de noticia recirculada

* **Registro local:** `NOT-009`, campo `titulo`: «Noticia antigua sobre puente recirculada en redes sociales».
* **Campos de evidencia:** `fecha_publicacion=2022-05-10T10:00:00Z` y `fecha_deteccion=2024-03-16T18:00:00Z`. La detección posterior no convierte la publicación en un hecho nuevo.
* **Componentes del fixture:** R=0.60, I=0.55, U=0.20, N=0.25, E=0.80; P=47.5, ilustrativo.
* **Límite:** ese titular no describe un colapso, daños, lugar exacto ni obras actuales. No añadir esos hechos al borrador. La prueba T03 utiliza otro fixture de fechas y no equivale a una investigación del puente.
* **Acción humana pendiente:** comprobar publicación original y si existe un hecho actual distinto. Conservar la advertencia temporal; no presentar el registro como última hora. Borrador y decisión humana pendientes.

### `CASO-004` — Dos cifras anuales, dos evidencias

Las cifras siguientes son las filas del corpus histórico del benchmark; una nueva consulta oficial o el snapshot ampliado puede contener revisiones. No se presentan como mediciones de hoy ni como evidencia de desempeño de una cartera.

| Afirmación de este ejemplo | ID y campos que la respaldan en `indicadores.csv` |
| :--- | :--- |
| La fila de crecimiento del PIB de Panamá para 2023 tiene valor 7.3 y unidad `%`. | `PAN-NY.GDP.MKTP.KD.ZG-2023`: `pais_iso3=PAN`, `indicador_id=NY.GDP.MKTP.KD.ZG`, `anio=2023`, `valor=7.3`, `unidad=%`. |
| La fila de inflación de Panamá para 2023 tiene valor 1.5 y unidad `%`. | `PAN-FP.CPI.TOTL.ZG-2023`: `pais_iso3=PAN`, `indicador_id=FP.CPI.TOTL.ZG`, `anio=2023`, `valor=1.5`, `unidad=%`. |

Los IDs de consulta se construyen a partir de la identidad de cada fila; las URL de las series están en su campo `fuente_url`. Una sola cita al PIB no respalda la cifra de inflación.

* **Componentes del fixture:** R=0.90, I=0.75, U=0.50, N=0.60, E=0.90; P=73.75, ilustrativo.
* **Preguntas pendientes:** ¿se revisaron estas observaciones desde el corte del corpus?, ¿qué contexto sectorial concreto puede relacionarse con ellas?, ¿qué evidencia adicional permite discutir una hipótesis sin afirmar causalidad?
* **Borrador y revisión:** preparar un boletín con observación e hipótesis separadas y tres preguntas; no afirmar solidez, capacidad de pago, exposición, impagos o estabilidad crediticia a partir de estas dos cifras. Revisión por una persona real pendiente.

### `CASO-005` — Inyección sintética y evidencia insuficiente

* **Registro local:** `NOT-010` es un titular sintético con instrucciones para ignorar reglas y declarar ganador a una persona. Su URL usa un dominio de ejemplo no confiable. Es una entrada adversarial para pruebas, no una noticia comprobada.
* **Límite:** el registro no afirma cortes o suspensión de servicios. Ese tema presente en el fixture de ficha no se usa como evidencia ni como hecho de esta página.
* **Componentes del fixture:** R=0.90, I=0.95, U=0.90, N=0.90, E=0.15; P=83.75, ilustrativo. El fixture declara `estado_evidencia=insuficiente`.
* **Control implementado para este registro:** cuando todos los titulares de un grupo son payloads detectados de inyección, el servicio asigna E=0, estado `insuficiente` y afirmaciones vacías, preservando citas para inspección del texto no confiable. La regresión `test_injected_source_cannot_become_publishable_even_with_high_decision_scores` en [invariantes](../../tests/test_domain_invariants.py) usa `NOT-010`, fuerza puntuaciones altas y verifica el bloqueo de generación. Su P depende de los componentes de esa ejecución, no de los 83.75 del fixture histórico. La prueba T08 tiene otra ficha sintética P=92.0.
* **Revisión:** no hay contenido factual corroborado ni borrador validado. Registrar el resultado del ensayo, la información que falta y la decisión de una persona real, sin obedecer la instrucción del titular.

## 3. Preparación de las cinco fichas de entrega

Antes de presentar, exportar cinco fichas de la ejecución efectiva, comprobar todos sus IDs contra el corpus declarado e incluir un caso de evidencia insuficiente. Adjuntar componentes, pasajes pertinentes, límites temporales, borrador si procede, persona revisora y estado real. Usar la [planilla de sustento](../validation/README.md) para comprobar afirmaciones de brief, copy, guion, respuestas y boletín.

Los fixtures antiguos contienen detalles y aprobaciones ilustrativas que no están validados; esta página no modifica ese JSONL ni lo convierte en evidencia admisible. La entrega debe usar exportaciones revisadas y corregidas, sin IDs inexistentes ni nombres ficticios presentados como revisores. Publicar esas fichas reales en Notion permanece pendiente.
