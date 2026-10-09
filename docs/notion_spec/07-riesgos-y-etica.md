# 07 — Riesgos, Ética y Controles para Revisión

> Contenido local preparado. Publicación y revisión de derechos, personas responsables y evidencias en Notion pendientes.

## 1. Principios de uso y límites comprobados

El copiloto ofrece evidencia disponible, señales y preguntas para investigación. El puntaje no es probabilidad de verdad ni de pérdida; no clasifica definitivamente noticias como verdaderas/falsas y no toma decisiones bancarias sobre clientes.

Los borradores generados entran en `en_revision`. La revisión puede registrar `requiere_evidencia`, `aprobado_como_borrador` o `descartado`; aprobar un borrador no publica una noticia. La API registra persona y notas como datos de la revisión; un nombre en un fixture o en un campo de texto no acredita identidad, cargo o revisión real.

Toda afirmación factual debe poder vincularse a fuente, campo/pasaje, fecha y alcance. Resolver un ID, validar un fragmento o comprobar términos no demuestra implicación semántica ni cobertura de todas las oraciones libres. La [adjudicación humana](../validation/README.md) de respuestas y borradores permanece pendiente.

## 2. Matriz de riesgos y evidencia local

La valoración de severidad es cualitativa de planificación; no una medición de frecuencia de incidentes.

| Riesgo | Severidad | Control y alcance | Evidencia / pendiente |
| :--- | :--- | :--- | :--- |
| Cifras, detalles o atribuciones no sustentadas | Crítica | Consultas extractivas o abstención; guardas de citas estructuradas, fragmentos, términos y negación. No sustituye revisión semántica del texto completo. | T06, T09 parcial, [consultas](../../tests/test_query_and_banking.py), [safety](../../tests/test_safety.py); veredictos humanos pendientes. |
| Inyección desde fuentes | Alta | Aislamiento de datos, escape de marcas/atributos XML y detección de patrones. Cobertura limitada a ataques probados; no resistencia universal. | T07, [safety](../../tests/test_safety.py), [invariantes](../../tests/test_domain_invariants.py). |
| Recirculación temporal | Alta | El agrupador compara fechas de calendario y marca una brecha superior a **tres días**, según su regla actual. Conserva fecha original; una diferencia temporal no prueba por sí sola el contexto periodístico del evento. | T03, [invariantes](../../tests/test_domain_invariants.py); revisar publicación y acontecimiento con una persona. |
| Confundir volumen con corroboración | Alta | Conservar IDs y procedencia; contar medios repetidos no acredita fuentes independientes. El servicio no interpreta pluralidad de medios como verificación cruzada. | T02, [consultas](../../tests/test_query_and_banking.py); linaje e independencia reales pendientes de revisión. |
| Borrador pese a evidencia insuficiente | Crítica | `can_publish_draft()` bloquea una ficha `insuficiente` incluso si P es alto. Un grupo compuesto únicamente por payloads de inyección detectados conserva citas para inspección, E=0 y afirmaciones vacías; los demás casos siguen sujetos a revisión. | T08 y regresión con `NOT-010` en [invariantes](../../tests/test_domain_invariants.py). |
| Imputación de ausencia como cero | Alta | Indicadores mantienen `None`/`NULL`. El fetcher USGS conserva nulos; almacenamiento permite nulos de actualización/coordenadas. El loader excluye features incompatibles y el snapshot rechaza entradas incompletas sin sustituir sus valores. No se acredita conservación universal en todas las entradas del adaptador. | [Loaders](../../tests/test_data_loaders.py), [snapshot](../../tests/test_sqlite_snapshot.py), [diccionario](../DATA_DICTIONARY.md). `EventoGeoJSON` sigue no nullable. |
| Sesgo de priorización | Media | Componentes, pesos y desempate visibles para discusión. La fórmula explicable no acredita ausencia de sesgo ni utilidad editorial general. | [Scoring](../../tests/test_scoring.py); selección independiente por editor pendiente. |
| Derechos de reutilización | Alta | Registrar fuente, alcance, condiciones y material efectivamente reutilizado; entregar metadatos y receta si el contenido no permite redistribución. | [Catálogo](03-catalogo-de-datos.md); comprobación de condiciones/autorizaciones concretas pendiente. |
| Exagerar IA o resultados de evaluación | Alta | Identificar proveedor efectivo y fallback; separar desarrollo, etiquetas expuestas y custodia externa. Tokens/costo no medidos se declaran pendientes. | [Métricas](06-pruebas-y-metricas.md), [ADR-0026](../adr/0026-human-adjudication-and-effective-model-reporting.md); ejecución NLP/ML sustantiva y evaluación humana pendientes. |

## 3. Derechos y alcance por fuente

* **TVN y medios enlazados:** usar inicialmente titulares/metadatos. El patrocinio y GDELT no transfieren derechos de artículos, imágenes o videos. Reutilizar extractos o cuerpos completos solo conforme a condiciones aplicables o autorización; no simular lectura del artículo completo. Si falta contenido, indicar «basado únicamente en titular/metadatos».
* **Banco Mundial:** el documento identifica CC BY 4.0 como licencia general; registrar atribución y comprobar excepciones de terceros. Conservar país, año, unidad y posibles revisiones; una cifra anual histórica no es una medición de hoy.
* **USGS:** conservar ID, URL, tiempo, magnitud y ubicación bajo condiciones aplicables; revisar elementos de terceros. La caja regional no equivale a Panamá. Usar como señal interna de hechos sísmicos para revisión, sin inferir inundaciones, daños o pérdidas que no consten en la evidencia.
* **GDELT:** usar metadatos y enlaces para recuperación y contexto. No describir todos los artículos encontrados como dominio público ni equiparar volumen o tono negativo con fraude, daño o confirmación.
* **SBP opcional:** no afirmar recopilación de informes que no esté documentada. Si se añade, conservar período, unidad y página y separar el análisis del equipo de opiniones oficiales.

## 4. Privacidad, atribución y acceso

La finalidad es utilizar fuentes públicas y datos agregados, evitando datos personales innecesarios, perfiles sensibles y listas de supuestos delincuentes o clientes riesgosos. Que una publicación sea pública no garantiza que carezca de datos personales; revisar los textos y la necesidad de almacenarlos o mostrarlos. Las acusaciones deben atribuirse como declaraciones y no como hechos probados.

Notion debe compartirse con participantes y jurado autorizados. La URL accesible al jurado no exige publicación del espacio en la web; confirmar puestos/invitados y permisos Business. No incluir credenciales en código, páginas, prompts, logs o capturas. La documentación pública utiliza `.env.example` y configuración sin secretos; no copiar `.env`.

## 5. Límites de la extensión bancaria

El boletín es contexto de entorno económico, logístico y sectorial. Separar observación de hipótesis de impacto y formular preguntas para una persona analista. No recomendar compra/venta, evaluar solvencia individual, conceder o denegar crédito, inferir pérdidas/impagos o exposición de una cartera inexistente ni emitir alertas regulatorias definitivas.

## 6. Verificaciones humanas pendientes

Asignar responsables; revisar sustento de al menos treinta afirmaciones si se producen tantas y los borradores completos; verificar derechos del material concreto, custodia de etiquetas, acceso a Notion y ensayo offline. Registrar resultados reales, fallos y correcciones. Una suite verde, un manifiesto o una planilla vacía no acreditan esas tareas.
