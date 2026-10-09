# 01 — Inicio del Reto: Copiloto de Inteligencia Informativa con IA

> Contenido local preparado para Notion Business. Publicación, identificación de participantes y acceso del jurado pendientes.

## 1. Equipo, modalidad y responsabilidades

El nombre de equipo utilizado en la documentación local es **Sentria**. La modalidad principal es **TVN editorial**; el boletín bancario es una extensión de análisis de entorno. Confirmar el registro del equipo y asignar personas reales en Notion antes de la presentación.

| Responsabilidad | Persona | Trabajo |
| :--- | :--- | :--- |
| Dominio y arquitectura | Pendiente de asignación | Contratos, scoring y límites de generación. |
| Datos y reproducibilidad | Pendiente de asignación | Ingesta, auditoría de cobertura y snapshot local. |
| Producto y experiencia editorial | Pendiente de asignación | Agenda, fichas, consultas y recorrido de revisión. |
| Evaluación y ética | Pendiente de asignación | Pruebas, revisión humana del sustento, derechos y custodia de evaluación. |

Los responsables de tareas y revisores deben registrarse durante el trabajo. Un rol propuesto o un nombre incluido en fixtures no acredita participación ni aprobación humana.

## 2. Problema y usuario

Un editor debe revisar fuentes dispersas, reconocer duplicados, identificar qué evidencia existe y preparar una pieza con preguntas pendientes. Repetir una fuente no confirma lo publicado. Una fecha de detección reciente tampoco convierte en nuevo un hecho antiguo.

El usuario principal es el **editor o periodista de TVN Media**. Su resultado útil es una agenda investigable, una ficha con atribución y un borrador por formato para revisión. El productor digital puede usar propuestas de titular y copy. Un analista bancario puede consultar contexto económico y logístico agregado, sin evaluar clientes.

El objetivo es asistir esas decisiones y reducir el trabajo de búsqueda y comprobación. El ahorro de tiempo es una **hipótesis pendiente de medición** con una tarea equivalente manual y asistida; no se afirma aumento de audiencia, ingresos o reducción del riesgo bancario.

## 3. Alcance del producto

| Capacidad | Resultado y límite |
| :--- | :--- |
| Carga y consultas locales | Corpus público de referencia y snapshot SQLite declarados; sin necesidad de un servidor de base de datos. |
| Agenda | Ranking explicable con `P = 30R + 25I + 20U + 15N + 10E`, componentes y desempate por urgencia e ID. El puntaje no es probabilidad de verdad. |
| Fichas | Fuentes, pasajes, fechas y vacíos de verificación. Los casos locales no equivalen a investigación periodística concluida. |
| Contexto oficial | País, período y unidad de indicadores; eventos USGS utilizados exclusivamente para hechos sísmicos pertinentes. |
| Paquete editorial | Brief de hasta 250 palabras, titular, enfoque, tres preguntas, verificaciones pendientes, guion de 45–60 segundos y copy de hasta 80 palabras. |
| Revisión humana | El borrador entra en `en_revision`; una persona puede aprobarlo como borrador, pedir evidencia o descartarlo. Aprobar no publica noticias. |
| Extensión bancaria | Boletín de entorno con observación e hipótesis separadas. No recomienda compra/venta ni infiere impagos, pérdidas o exposición de una cartera inexistente. |

Quedan fuera del alcance la publicación automática, calificación definitiva de noticias como verdaderas/falsas, perfilamiento sensible, riesgo individual de crédito, datos privados de clientes y recuperación detrás de paywalls.

## 4. Criterios de éxito y estado de validación

* **Trazabilidad:** cada afirmación factual debe citar evidencia pertinente. Los controles automáticos verifican IDs, fragmentos y condiciones léxicas conservadoras; no prueban implicación semántica ni cobertura completa de todo el texto libre. La [revisión humana](../validation/README.md) está preparada y sus veredictos permanecen pendientes.
* **Reconocer vacíos:** las consultas sin evidencia deben abstenerse y explicar lo faltante; las contradicciones deben mostrar versiones y revisión pendiente. Las pruebas y el benchmark cubren casos controlados, no una tasa general de ausencia de alucinaciones.
* **Uso efectivo de IA:** la [ejecución real de Jev](../validation/decision_jev_2026-10-09.json) conserva diez predicciones de contradicción, sin fallback, frente a regex. Son pares sintéticos expuestos de desarrollo; la comparación con etiquetas editoriales independientes sigue pendiente. El mock no acredita desempeño remoto.
* **Reproducibilidad:** identificar commit, corpus, corte, manifiesto, proveedor efectivo y fallback. Consultar el resultado y número de pruebas en la **última ejecución de `make check`**, junto con el benchmark y sus fallos.
* **Notion:** publicar las ocho páginas, incorporar responsables y registros reales durante la ejecución, verificar permisos y presentar desde Notion. El contenido local por sí solo no acredita habilitación.

## 5. Accesos y siguiente paso humano

* [Índice de páginas para Notion](README.md): URL del espacio y acceso del jurado pendientes de registrar.
* [Repositorio GitHub declarado](https://github.com/evallesv/hackiathon-reto-tvn): verificar acceso del jurado y que incluya la versión presentada.
* Prototipo local: `http://localhost:8080/`; OpenAPI: `http://localhost:8080/docs`. Iniciar con el comando del README del proyecto y ensayar con el snapshot y proveedores identificados.
* [Casos y evidencias](05-casos-y-evidencias.md), [pruebas y métricas](06-pruebas-y-metricas.md) y [pitch de diez minutos](08-presentacion-al-jurado.md).

Asignar una persona editorial que revise las afirmaciones y los borradores completos, publicar su resultado real en Notion y ensayar la demo offline. La disponibilidad de una URL de producción no se utiliza aquí como evidencia de despliegue o de acceso verificado.
