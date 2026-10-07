# ADR-0003: Motor de Puntaje de Atención Explicable e Independencia del Estado de Evidencia

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

La sección 4 del reto estipula una herramienta de ordenamiento (puntaje de atención) de 0 a 100 con la siguiente especificación:
* $P = 30R + 25I + 20U + 15N + 10E$
* Componentes normalizados en $[0, 1]$.
* Rangos sin solapamiento: bajo $[0, 40)$, medio $[40, 70)$, alto $[70, 100]$.
* Criterio de desempate: mayor urgencia ($U$), seguido por ID alfanumérico.
* **Restricción crítica**: El estado de evidencia (`insuficiente`, `parcial`, `suficiente_para_borrador`) es **estrictamente independiente** del puntaje de atención.
* Un puntaje alto con evidencia insuficiente exige investigación y **no habilita publicación de borrador** (Prueba T08).
* El sistema **no debe etiquetar automáticamente una noticia como verdadera o falsa**.

## Decisión

1. Crear `ScoringEngine` en el dominio puro (`src/hackiathon_reto_tvn/domain/scoring.py`).
2. Validar que cada componente ($R, I, U, N, E$) esté estrictamente acotado en $[0.0, 1.0]$.
3. Implementar ordenamiento compuesto en Python: `(-c.puntaje, -c.componentes.urgencia, c.id_caso)`.
4. Implementar `can_publish_draft(caso)` que bloquea la habilitación de borradores si `estado_evidencia == INSUFICIENTE`, retornando una advertencia explícita.
5. Dejar la decisión final de publicación y verificación en manos de la persona revisora mediante la máquina de estados: `nuevo`, `en_revision`, `requiere_evidencia`, `aprobado_como_borrador`, `descartado`.

## Consecuencias

### Positivas
* Cumplimiento estricto con las pruebas de aceptación T08 y las directrices éticas del hackathon.
* Explicabilidad total: cada cálculo expone el desglose de sus 5 componentes y la versión de las reglas aplicadas.
