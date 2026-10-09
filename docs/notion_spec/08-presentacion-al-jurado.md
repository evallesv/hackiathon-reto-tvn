# 08 — Presentación al Jurado desde Notion

> Contenido local preparado. Publicación, acceso del jurado y ensayo desde Notion pendientes.

## 1. Recorrido de diez minutos

El pitch parte de la página «Presentación al jurado» en Notion y navega por las páginas de trabajo. Se permiten enlaces o embeds al prototipo y GitHub. Un dashboard, PDF o presentación de diapositivas por separado no sustituye este recorrido.

| Tiempo | Contenido | Página de Notion y evidencia |
| :--- | :--- | :--- |
| 0:00–1:00 | Problema, usuario y valor para TVN | Inicio del reto: editor que debe escoger temas investigables y preparar borradores. |
| 1:00–2:00 | Solución, alcance y datos públicos | Catálogo de datos: identificar el snapshot de demo, su corte, procedencia y hash. |
| 2:00–6:00 | Demo: consulta útil, ficha con citas, borrador y abstención | Casos y evidencias → enlace al prototipo; registrar la revisión del borrador. |
| 6:00–8:00 | Arquitectura, capacidad IA, baseline y métricas observadas | Diseño de solución y Pruebas y métricas: proveedor efectivo, resultados y un fallo/corrección reales. |
| 8:00–9:00 | Valor operativo medido o hipótesis identificada | Inicio del reto: objetivo de reducir búsqueda y comprobación; declarar si falta ensayo manual frente a asistido. |
| 9:00–10:00 | Riesgos, limitaciones y próximos pasos | Riesgos y ética y Plan y decisiones: controles, tareas pendientes y reserva humana. |

Añadir cinco minutos para preguntas del jurado, según la sección 11 del PDF.

## 2. Guion y acciones del expositor

### 0:00–1:00 — Problema y usuario

«Nuestro usuario es un editor de TVN. Debe encontrar temas relevantes entre fuentes dispersas, distinguir repetición de corroboración y decidir qué falta investigar. El copiloto organiza esas señales, muestra la evidencia disponible y prepara un borrador para una decisión humana.»

Mostrar usuario y alcance en «Inicio del reto». No atribuir ahorros, audiencia o resultados financieros que no se hayan medido.

### 1:00–2:00 — Solución y datos

«Usamos noticias públicas y series oficiales. Los titulares ayudan a descubrir temas; los indicadores aportan contexto anual y USGS respalda hechos sísmicos. El snapshot SQLite contiene el corpus local de demostración y permite consultar sin internet. La base operativa almacena ingesta y revisiones. Los períodos históricos permanecen visibles y no se describen como cifras de hoy.»

Abrir «Catálogo de datos» y el manifiesto efectivo. Identificar corpus, corte y versión usados en el ensayo. Explicar la diferencia entre el corpus histórico del benchmark y el snapshot ampliado, si ambos se utilizan.

### 2:00–6:00 — Demostración de extremo a extremo

1. Desde «Casos y evidencias», abrir el prototipo y consultar cinco temas para la agenda. Mostrar componentes de `P = 30R + 25I + 20U + 15N + 10E`, urgencia y vacíos de verificación. Usar los IDs y puntajes de la ejecución, evitando valores fijos tomados de fixtures históricos.
2. Abrir una ficha económica y una fuente oficial pertinente. Consultar una cifra anual presente en el corpus del ensayo, mostrando país, año, unidad, ID y pasaje/campo de origen. Si solo existen titulares, señalar «basado únicamente en titular/metadatos». No forzar una relación causal entre noticia e indicador.
3. Generar un borrador permitido por el estado de evidencia. Mostrar brief de hasta 250 palabras, tres preguntas, guion de 45–60 segundos y copy de hasta 80 palabras. Explicar las comprobaciones automáticas efectivas y lo que sigue requiriendo revisión humana. Aprobar como borrador no publica una noticia.
4. Registrar una revisión real con persona responsable y notas; crear o actualizar manualmente la ficha correspondiente en Notion. Si no hay revisor disponible en el ensayo, dejar la revisión pendiente. Los nombres y aprobaciones de fixtures no cuentan como evidencia humana.
5. Hacer una pregunta cuya respuesta no exista en el corpus. Mostrar abstención explícita y qué información falta. Abrir también el caso de prioridad alta con evidencia insuficiente: la prioridad exige investigación y no habilita publicación.

Si aparece una contradicción, presentar ambas versiones, fechas y alcance sin escoger arbitrariamente. Con varias publicaciones, mostrar procedencia y explicar que repetir una agencia no crea fuentes independientes.

### 6:00–8:00 — IA y evaluación

«Separamos las reglas de dominio de los adaptadores de decisión y generación. Mostramos aquí el proveedor y modelo realmente utilizados. El modo mock permite ensayar el flujo offline; su latencia y sus reglas no acreditan desempeño de un modelo remoto ni una capacidad NLP sustantiva. La contribución de IA debe demostrarse con una ejecución identificada y comparada contra un baseline.»

Abrir «Diseño de solución» con versiones, prompts y parámetros públicos, y «Pruebas y métricas» con la última salida de `make check` y del benchmark. Informar entorno, numerador, denominador y fallos; distinguir IDs resolubles, coincidencia literal y revisión humana de soporte. La comparación actual por palabras clave es exploratoria mientras no exista selección independiente de un editor.

Las etiquetas reservadas expuestas en el repositorio no son ciegas. Una evaluación independiente requiere un conjunto nuevo bajo custodia externa. Mostrar tokens y costo medidos si existen; si no, declarar que no se midieron. No atribuir latencias mock a los proveedores comerciales.

Mostrar en Notion una prueba fallida real y su corrección, con evidencia reproducible. Si no está documentada todavía, marcarla pendiente y completarla antes del cierre; no inventar resultados.

### 8:00–9:00 — Valor operativo

«Nuestra hipótesis de valor es reducir el tiempo que un editor dedica a buscar fuentes, reconocer vacíos y preparar una primera pieza. Para medirla debemos comparar una tarea equivalente manual y asistida, registrando número de pruebas y tiempo. Mientras ese ensayo no exista, presentamos el valor como hipótesis.»

Si se realizó el ensayo, mostrar su método y resultados efectivos. No inferir aumento de audiencia, rentabilidad o reducción del riesgo bancario con estos datos.

### 9:00–10:00 — Riesgos y próximos pasos

«Los textos de fuentes se tratan como datos no confiables. El sistema conserva nulos y períodos, evita publicación automática y mantiene revisión humana. Las comprobaciones de citas no sustituyen comprobar el sustento semántico. La agenda presenta evidencia y preguntas; no clasifica noticias como verdaderas o falsas.»

Mostrar condiciones por fuente, límites del control de inyección, evaluación humana y tareas pendientes. La banca es una extensión de análisis de entorno: no se infieren pérdidas, impagos o exposición de una cartera inexistente. Cerrar con el siguiente paso concreto de validación con una persona editorial.

## 3. Ensayo y contingencia offline

Antes del cierre, verificar el acceso de jurado a Notion y GitHub y registrar fecha, persona y resultado. Ensayar el flujo con el snapshot declarado y proveedores mock, sin ingesta en red. Guardar la evidencia en «Pruebas y métricas» y preparar las fichas utilizadas.

El fallback local permite demostrar consultas y controles disponibles con ese corpus. Debe identificarse cuando se usa; no presentar una salida mock como ejecución del modelo remoto. Si una función o fuente no está disponible, mostrar la limitación y el comportamiento observado.

El estado y el número de pruebas se consultan en el **último `make check` ejecutado**; no usar un conteo fijo en el discurso. Una suite verde no prueba por sí sola relevancia editorial, soporte semántico o resistencia a todos los ataques.

## 4. Respuestas a pruebas dinámicas del jurado

* **«¿De dónde viene esta cifra y de qué año es?»** Abrir el ID, campo/pasaje, URL oficial, país, año y unidad; distinguir período del dato y fecha de extracción.
* **«Si cinco medios replican una agencia, ¿cuántas fuentes independientes cuentas?»** Una procedencia; mostrar los registros sin atribuir independencia que no esté verificada.
* **«¿Qué pasa si falta evidencia o la fuente cambia las instrucciones?»** Demostrar el caso concreto de abstención o aislamiento, indicando alcance y limitaciones de las pruebas.
* **«Muéstrame una decisión, una prueba fallida y su corrección en Notion.»** Navegar a los registros efectivos con responsable, fecha, ejecución y corrección; los Markdown locales sirven como insumo hasta publicarlos.
* **«¿La fórmula elimina sesgos?»** No. Sus componentes visibles permiten inspeccionar y discutir criterios; la transparencia no acredita ausencia de sesgos.
