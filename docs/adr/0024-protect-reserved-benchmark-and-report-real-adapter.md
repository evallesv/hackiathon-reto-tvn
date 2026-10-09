# ADR-0024: Proteger la evaluación reservada y reportar el adaptador ejecutado

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Área**: Evaluación / Benchmark

## Contexto

El runner ejecutaba las 60 consultas, incluidas 20 con etiquetas reservadas que están versionadas en el mismo repositorio. Además, la métrica llamada System One se generaba mediante una regla regex con una excepción manual, sin llamar al adaptador de decisión. El evaluador de ranking también podía comparar la recencia de un corpus con una agenda obtenida de la base operacional local.

## Decisión

- La API y `make benchmark` ejecutan solo las 40 consultas de desarrollo. La solicitud de ejecutar todas las filas se rechaza mientras el conjunto reservado carezca de custodia externa.
- La métrica de contradicciones obtiene predicciones de `CopilotService.detect_contradictions`, calcula Macro-F1 y reporta proveedor/modelo. Los resultados del `mock` se identifican como deterministas y no se atribuyen a un modelo remoto.
- El baseline de recencia y el puntaje P usan el mismo corpus sellado; la base operacional local se deshabilita para esa comparación.
- Si P@5 del baseline es cero, la mejora relativa es `null` y la interfaz la muestra como `N/D`.

## Consecuencias

- La suite de desarrollo permanece reproducible y no consume etiquetas reservadas.
- El modo `mock` permite ensayar el protocolo offline, pero no demuestra una mejora frente a regex.
- Las 20 etiquetas ya presentes en el historial/repositorio están expuestas. El código no puede convertirlas retrospectivamente en un conjunto ciego; se requiere custodia externa para una evaluación independiente.
- P@5 sigue usando etiquetas heurísticas por palabras clave y contradicciones se mide sobre diez pares sintéticos; ambas son exploratorias.

## Conformidad con el reto

Evita reportar datos de desarrollo como resultados ciegos y enlaza cada métrica del modelo con el adaptador realmente ejecutado, a la vez que mantiene clara la limitación pendiente de custodia externa.
