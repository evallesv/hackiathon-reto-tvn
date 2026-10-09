# 06 — Pruebas y Métricas del Sistema

> **Espacio Oficial de Presentación en Notion Business**  
> **Matriz de Pruebas de Aceptación (T01 a T10), Benchmark de 60 Consultas y Comparativa de Baselines**

---

## 1. Matriz de Pruebas de Aceptación Obligatorias (T01 – T10)

Todas las pruebas se ejecutan de manera automatizada mediante `pytest` con ejecución 100% determinista y offline:

| Test ID | Criterio de Aceptación Oficial | Resultado Esperado | Resultado Observado | Archivo de Prueba | Estado |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **T01** | Fechas inválidas o valores nulos en CSV no provocan caídas del sistema. | Segregar filas inválidas y preservar valores ausentes. | Una fila sin título se excluye y dos se cargan; la fecha original inválida se conserva como texto. Las pruebas de indicadores comprueban `None` sin imputar ceros. | `test_acceptance_t01_t10.py::test_t01_*`, `test_data_loaders.py` | **PASÓ** |
| **T02** | Múltiples artículos que reportan el mismo evento se agrupan sin perder procedencia. | Tres titulares sintéticos sobre nuevo calado ACP forman un grupo. | Un grupo conserva los tres IDs. Es agrupación léxica; no prueba independencia de medios ni resolución semántica general. | `test_acceptance_t01_t10.py::test_t02_*` | **PASÓ** |
| **T03** | Una noticia recirculada de años anteriores conserva su fecha de publicación original. | Noticia del `2022-04-15` detectada en marzo de 2024 se identifica como recirculada. | La advertencia contiene la fecha original y la instrucción de conservarla. Esta prueba no mide por sí sola la urgencia del ranking. | `test_acceptance_t01_t10.py::test_t03_*` | **PASÓ** |
| **T04** | Los indicadores históricos del Banco Mundial conservan año exacto, país y unidad. | El registro de PIB de Panamá de 2023 conserva valor 7.3 y unidad `%`. | El loader conserva país, año, valor y unidad; las consultas y citas se prueban además en `test_query_and_banking.py`. | `test_acceptance_t01_t10.py::test_t04_*`, `test_query_and_banking.py` | **PASÓ** |
| **T05** | Versiones contradictorias entre fuentes se exponen lado a lado con verificación pendiente. | Comparar dos textos sintéticos que afirman 15 y 28 millones de inversión. | En mock: `discrepancia_detectada: True`, dos versiones y estado `requiere_evidencia`; no escoger una cifra arbitrariamente. | `test_acceptance_t01_t10.py::test_t05_*` | **PASÓ** |
| **T06** | Una consulta sin evidencia en el corpus emite abstención explícita sin alucinar. | Formatear la ausencia de registros de producción de litio de Panamá en 2025. | El formateador emite `[ABSTENCIÓN EXPLÍCITA]`; pruebas de consultas y benchmark comprueban también la ruta de servicio. No demuestra ausencia general de alucinaciones. | `test_acceptance_t01_t10.py::test_t06_*`, `test_query_and_banking.py` | **PASÓ** |
| **T07** | Intentos de inyección de prompt dentro de fuentes son neutralizados y tratados como datos. | Patrones `"IGNORA INSTRUCCIONES"` neutralizados dentro de `<source_data>`. | El payload probado se neutraliza; la prueba no acredita resistencia frente a todos los ataques. Las pruebas de safety comprueban además escape y aislamiento XML. | `test_acceptance_t01_t10.py::test_t07_*`, `test_safety.py` | **PASÓ** |
| **T08** | Alto puntaje de atención con evidencia insuficiente bloquea publicación de borrador. | Caso sintético con $P = 92.0$ y evidencia insuficiente. | `can_publish_draft() == False` y motivo de investigación. Los guardas de generación se prueban además en `test_domain_invariants.py`. | `test_acceptance_t01_t10.py::test_t08_*`, `test_domain_invariants.py` | **PASÓ** |
| **T09** | El brief editorial generado distingue hechos de declaraciones, inferencias e hipótesis. | Las afirmaciones estructuradas incluyen citas cuyo ID y fragmento existen; los términos de contenido deben aparecer en los pasajes citados. | Control léxico conservador sobre `afirmaciones`; no demuestra implicación semántica ni extrae automáticamente todas las afirmaciones del texto libre. | `test_acceptance_t01_t10.py::test_t09_*`, `test_safety.py` | **PARCIAL** |
| **T10** | Prototipado y demo funcionan sin conexión a internet ni tokens de pago externos. | Generar agenda con mock y trabajar sobre una copia temporal del corpus. | Tres casos con puntaje positivo; el manifiesto original no cambia. La suite fuerza mocks e ingesta deshabilitada; no acredita un ensayo de demo con jurado. | `test_acceptance_t01_t10.py::test_t10_*`, `test_api.py`, `test_sqlite_snapshot.py` | **PASÓ** |

---

## 2. Benchmark Formal de 60 Consultas Etiquetadas

Para evaluar de forma cuantitativa y reproducible el desempeño del copiloto frente a baselines estándar, se diseñó y etiquetó un conjunto de **60 consultas evaluativas** en `data/benchmark.jsonl`:
- **40 consultas de desarrollo (Dev Set)**: Iteración interna de reglas y evaluación local.
- **20 consultas reservadas (Jury Set)**: Están en el repositorio y no son ciegas; requieren custodia externa para una evaluación independiente.
- Un holdout nuevo debe ser proporcionado como JSONL externo con filas `conjunto=reservado_jurado`; tanto el archivo como el reporte quedan fuera del repositorio. La ubicación externa no prueba independencia: registrar autoría, custodia y ausencia de exposición durante el ajuste.
- **Distribución de Tipologías**:
  - 30 consultas soportadas con hechos en el corpus (TVN, Banco Mundial, USGS).
  - 10 consultas de contradicción factual entre dos versiones.
  - 10 consultas con hechos faltantes (para evaluar abstención estricta).
  - 10 consultas con intentos adversariales de inyección de prompt y fuga de instrucciones.

### 2.1. Resultados locales exploratorios (2026-10-09)

El archivo contiene 60 consultas: 40 desarrollo y 20 reservadas. El endpoint ejecuta desarrollo. El conjunto reservado está dentro del repositorio, por lo que no es ciego ni constituye evaluación externa.

```
En ejecución offline del 2026-10-09 sobre `data/raw/` validado por manifiesto: P@5 recencia 0.200 (1/5) y fórmula P 0.400 (2/5), +100.0% relativo exploratorio.
La relevancia se infiere con palabras clave; no equivale a una selección independiente de editor.

En las 20 consultas sustentadas de desarrollo, el valor esperado principal y el ID de fuente coincidieron literalmente en 20/20 (100%). La medición no valida semántica y depende de etiquetas de desarrollo, no de adjudicación editorial independiente. El benchmark separa este valor del indicador de IDs resolubles.

Contradicciones: diez pares sintéticos comparados entre regex y el adaptador de decisión configurado. En modo `mock`, Macro-F1 fue 0.792 para regex y 0.524 para el mock (`mock-clef-offline`). No representa desempeño de un modelo remoto ni una muestra editorial independiente.

Citas/abstención: 20/20 respuestas sustentadas citaron IDs existentes; abstención y marcador adversarial se detectaron en todos los casos de prueba seleccionados. No comprueba que cada afirmación esté citada ni el soporte semántico.
Latencia: consultar mediana y p95 en data/benchmark_results.json para la ejecución vigente; no atribuir tiempos mock a un proveedor real.
```

---

## 3. Resumen Comparativo de Baselines

### Ejecución real de decisión (2026-10-09)

El [reporte Jev](../validation/decision_jev_2026-10-09.json) guarda las diez entradas, etiquetas de
desarrollo, predicciones, probabilidades y latencias. Jev `jev-1.13-free` obtuvo Macro-F1 **1.000**
frente a **0.792** del baseline regex, con **10/10** predicciones coincidentes y **0/10** fallbacks.
Mediana **609.280 ms** y p95 **863.804 ms** en este entorno. Son diez pares sintéticos expuestos,
con etiquetas creadas para desarrollo; no demuestran generalización ni validación editorial independiente.
La respuesta no proporcionó tokens reconocibles en `usage`; tokens y costo permanecen sin dato verificado.
El nombre `free` del modelo no constituye una medición de costo.

| Componente del Sistema | Baseline Clásico | Solución Copiloto IA (Sentria) | Impacto / Ganancia |
| :--- | :--- | :--- | :--- |
| **Ranking de Agenda (CU-01)** | Recencia sobre los mismos cinco casos. | Fórmula de atención sobre el mismo corpus congelado. | Resultado exploratorio: 1/5 frente a 2/5; relevancia por keywords, no etiqueta editorial; +100.0% relativo. |
| **Contradicciones** | Regla regex sobre números y verbos de negación. | Predicciones consultando el adaptador de decisión configurado. | En modo mock, Macro-F1 0.792 frente a 0.524; diez pares sintéticos, no representa evaluación editorial independiente. |
| **Citas y abstención** | No hay baseline. | IDs de fuente resolubles; coincidencia literal de valor + fuente esperados; recuento de marcadores. | 20/20 coincidencias literales en desarrollo. No prueba que cada afirmación esté citada, soporte semántico ni ausencia general de alucinaciones. |

---

## 4. Ejecución de la Suite de Calidad

Para reproducir la totalidad de las pruebas y métricas desde el entorno de terminal:

```bash
# Ejecutar los 10 tests de aceptación mandatorios
uv run pytest tests/test_acceptance_t01_t10.py -v

# Ejecutar el benchmark de desarrollo (40 consultas); no ejecuta las 20 etiquetas reservadas expuestas
make benchmark

# Ejecutar el Quality Gate completo (Ruff, Format, Mypy y Pytest)
make check
```

## 5. Fallos, falsas abstenciones y revisión humana

El reporte guarda respuestas y citas completas, numeradores/denominadores de abstención y listas de fallos
por ID. Las abstenciones incorrectas se cuentan sobre preguntas etiquetadas como respondibles; no se
excluyen del denominador de exactitud. La evaluación adversarial mide los marcadores especificados,
sin afirmar resistencia universal. Las predicciones de contradicciones identifican proveedor/modelo
efectivos y número de fallbacks, separados del adaptador configurado.

La [planilla de revisión humana](../validation/README.md) incluye registros originales del corpus para
adjudicar cada afirmación, persona y fecha. Prepararla no equivale a validarla: todos los veredictos
comienzan vacíos. La meta ≥90% de sustento y la muestra de al menos 30 afirmaciones, si existen tantas,
requieren revisión humana real. Los borradores completos deben revisarse además de las respuestas.

Tokens y costo se reportan como no medidos mientras no exista instrumentación de una ejecución real.
La ruta general de consultas ahora es extractiva: devuelve titulares/metadatos o abstención; las respuestas
libres del LLM no se presentan con citas asignadas automáticamente (ADR-0025).

Fallo y corrección reproducibles para Notion: la regresión `test_canal_answer_quotes_actual_measurement`
falló porque un titular de 44 pies producía una respuesta de 45 pies. Tras ADR-0025 se cita la cifra presente
en el titular. Las pruebas de alcance país/año, escape XML y negaciones también reprodujeron fallos antes
de su corrección. Publicar el commit, prueba, ejecución y responsable real en «Plan y decisiones».
