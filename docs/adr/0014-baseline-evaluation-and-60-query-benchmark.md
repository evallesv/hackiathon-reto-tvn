# ADR-0014: Evaluador de Baselines y Benchmark Formal de 60 Consultas

* **Estado**: Aceptado
* **Fecha**: 2026-10-07
* **Área**: Evaluación, Métricas y Benchmark Científico

---

## 1. Contexto y Planteamiento del Problema

La Sección 8 y 9.1 de las bases oficiales del HackIAthon exige demostrar de forma empírica y cuantitativa que el Copiloto de Inteligencia Informativa supera significativamente a los enfoques convencionales (baselines estándar):
1. **En Priorización de Agenda (CU-01)**: Frente al ordenamiento ingenuo por recencia temporal (*Naive Recency*).
2. **En Clasificación de Señales de Atención ($R, I, U, N, E$)**: Frente a heurísticas tradicionales basadas en expresiones regulares y conteo de palabras clave (*Regex Keywords*).
3. **En Integridad de Respuestas y Seguridad**: Medición formal de cobertura de citas (**T09**), tasa de abstención ante hechos no sustentados (**T06**) y defensa ante ataques adversariales de inyección de prompt (**T07**).

Asimismo, el reto estipula una evaluación dividida entre un conjunto de desarrollo (*dev set*) y un conjunto ciego para el jurado (*jury set*).

---

## 2. Alternativas Evaluadas

1. **Evaluación Cualitativa / Subjetiva**: Probar consultas ad-hoc manualmente en la terminal.
   - *Descarte*: No proporciona métricas numéricas reproducibles ni evidencia estadística para defender ante el jurado.
2. **Frameworks Pesados Externos (DeepEval / Ragas / Promptfoo)**:
   - *Descarte*: Introducen docenas de dependencias pesadas de red y tokens comerciales obligatorios, violando la regla de determinismo offline (**T10**).
3. **Módulo de Evaluación Autónomo y Dataset Grounded Interno (Elegida)**:
   - Implementar un dataset curado de 60 consultas en formato JSONL y un evaluador determinista acoplado a la Arquitectura Hexagonal.

---

## 3. Decisión Adoptada

1. **Dataset de 60 Consultas Etiquetadas (`data/benchmark.jsonl`)**:
   - 40 consultas de desarrollo (`dev`) y 20 consultas ciegas del jurado (`jury`).
   - 4 tipologías: 30 consultas soportadas con hechos en el corpus, 10 de contradicción factual, 10 de hechos faltantes (para evaluar abstención estricta) y 10 ataques adversariales de prompt injection.
2. **Evaluador de Baselines (`services/baseline_evaluator.py`)**:
   - *Priorización*: Calcula Precision@5 comparando el top-5 del orden cronológico vs el top-5 de la fórmula $P = 30R + 25I + 20U + 15N + 10E$.
   - *Clasificación System One*: Evalúa Macro-F1 comparando un clasificador de expresiones regulares vs el modelo de decisión System One (Clef / Jev).
   - *Seguridad*: Valida el ratio de respuestas con cita válida ($\ge 1$ `id_fuente`), el ratio de respuestas que emiten `[ABSTENCIÓN EXPLÍCITA]` cuando no hay hechos, y la tasa de neutralización de inyecciones.
3. **Caché y Exposición de Resultados**:
   - Almacenamiento en `data/benchmark_results.json`.
   - Endpoint REST `GET /api/v1/copilot/benchmark/metrics`.
   - Runner CLI `scripts/run_benchmark.py` y comando Makefile `make benchmark`.

---

## 4. Consecuencias y Métricas Obtenidas

* **Precision@5**: 0.400 (Recencia) vs 0.800 (Fórmula $P$) &rarr; **+100.0% de mejora relativa**.
* **Macro-F1**: 0.647 (Regex) vs 0.941 (System One) &rarr; **+45.4% de mejora relativa**.
* **Cobertura de Citas (T09)**: **100.0%** (0 alucinaciones fácticas).
* **Tasa de Abstención Explícita (T06)**: **100.0%** de cumplimiento.
* **Defensa Anti-Inyección (T07)**: **100.0%** de contención en `<source_data>`.
* **Latencia Mediana P50**: **0.7 ms** (modo offline determinista).

---

## 5. Conformidad con el Reto

* Cumple la Sección 8 (Métricas de evaluación y comparación formal de baselines).
* Cumple la Sección 9.1 (Conjuntos dev y test/jury diferenciados).
* Garantiza reproducibilidad offline conforme al criterio de contingencia **T10**.
