# ADR-0014: Evaluador de Baselines y Benchmark Formal de 60 Consultas

* **Estado**: Revisado; métricas iniciales invalidadas por auditoría local (2026-10-08)
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
2. **Evaluador actual (`services/baseline_evaluator.py`)**:
   - *Priorización*: estima Precision@5 con etiquetas por palabras clave; carece de relevancia editorial independiente.
   - *Contradicciones*: usa la misma regla regex para ambas predicciones con una excepción textual; no llama a System One. El F1 es de clase positiva, no macro-F1.
   - *Seguridad*: cuenta IDs y marcadores de respuesta; no mide soporte semántico ni resistencia general.
3. **Caché y Exposición de Resultados**:
   - Almacenamiento en `data/benchmark_results.json`.
   - Endpoint REST `GET /api/v1/copilot/benchmark/metrics`.
   - Runner CLI `scripts/run_benchmark.py` y comando Makefile `make benchmark`.

---

## 4. Consecuencias y límites de la medición

* Las cifras originales de **0.400/0.800 P@5**, **0.647/0.941 Macro-F1** y **+45.4%** no se reproducen y quedan retiradas.
* Reejecución offline del 2026-10-08: P@5 0.200 (recencia, 1/5) frente a 0.400 (fórmula P, 2/5), exploratorio.
* En diez pares sintéticos, F1 de clase positiva: 0.833 para regex y 0.833 para la regla mock. No evalúa un modelo real.
* Las tasas estructurales de citas, abstención y latencia no acreditan soporte semántico ni ausencia de alucinaciones.
* La API ejecuta desarrollo. El reservado está en el repositorio y no es ciego.

---

## 5. Conformidad con el Reto

* El runner permite medir el conjunto de desarrollo offline; no demuestra todavía una mejora de IA.
* La evaluación reservada requiere custodia y respuestas que no se usen para ajustar prompts o reglas.
* Una nueva medición debe guardar etiquetas humanas, salidas, commit, corpus y modo de ejecución.
