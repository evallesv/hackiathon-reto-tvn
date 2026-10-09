# 02 — Plan, Decisiones y Registro Verificable

> Contenido local preparado para Notion Business. Responsables personales, publicación y registro en el espacio real pendientes.

## 1. Backlog y evidencias del repositorio

El siguiente registro referencia commits existentes y pruebas localizables. «Implementado» describe código y comprobaciones automáticas; no equivale a aceptación editorial, publicación en Notion o evaluación independiente. Las responsabilidades humanas están pendientes de asignación.

| Tarea | Cambio y commit verificable | Evidencia local | Estado | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| TSK-01 | Snapshot SQLite: `444ab5f` | [Pruebas del snapshot](../../tests/test_sqlite_snapshot.py); [ADR-0019](../adr/0019-sqlite-offline-snapshot-package.md). | Implementado; revisar paquete efectivo del ensayo. | Por asignar. |
| TSK-02 | Límites de brief/copy/guion: `df26899` | [Invariantes editoriales](../../tests/test_domain_invariants.py); [ADR-0020](../adr/0020-editorial-deliverable-constraints.md). | Implementado; validación humana de piezas pendiente. | Por asignar. |
| TSK-03 | Identidad nullable de indicadores: `7021d1b` | [Loaders](../../tests/test_data_loaders.py); [ADR-0021](../adr/0021-preserve-missing-indicator-identifiers.md). | Implementado. | Por asignar. |
| TSK-04 | Agrupación léxica y manifiesto de solo lectura: `d93a6c6` | [Loaders](../../tests/test_data_loaders.py), [API](../../tests/test_api.py); [ADR-0022](../adr/0022-deterministic-news-event-grouping.md), [ADR-0023](../adr/0023-read-only-manifest-endpoint.md). | Implementado; agrupación semántica general no demostrada. | Por asignar. |
| TSK-05 | Benchmark aislado del corpus operativo: `3053178` | [Pruebas de evaluación](../../tests/test_benchmark_baseline.py); [ADR-0024](../adr/0024-protect-reserved-benchmark-and-report-real-adapter.md). | Desarrollo exploratorio; evaluación humana pendiente. | Por asignar. |
| TSK-06 | Validación de IDs citados: `8d2656a` | [Pruebas de evaluación](../../tests/test_benchmark_baseline.py). | Implementado; ID resoluble no prueba sustento semántico. | Por asignar. |
| TSK-07 | Resolución de indicador y metadatos: `664072d` | [Consultas y banca](../../tests/test_query_and_banking.py). | Implementado para los escenarios probados. | Por asignar. |
| TSK-08 | Runner para holdout externo: `4f5d8a5` | [Pruebas de evaluación](../../tests/test_benchmark_baseline.py). | Implementado; nuevo conjunto y custodia independiente pendientes. | Por asignar. |
| TSK-09 | Respuestas extractivas y guardas de borrador: `8b22419` | [Consultas](../../tests/test_query_and_banking.py), [safety](../../tests/test_safety.py), [invariantes](../../tests/test_domain_invariants.py); [ADR-0025](../adr/0025-corpus-grounded-query-and-draft-guards.md). | Implementado; revisión de soporte factual pendiente. | Por asignar. |
| TSK-10 | USGS incompleto sin imputación: `4da6c99` | [Loaders](../../tests/test_data_loaders.py), [snapshot](../../tests/test_sqlite_snapshot.py). | Implementado; registros incompletos se excluyen o bloquean el empaquetado. | Por asignar. |
| TSK-11 | Proveedor efectivo y planilla de adjudicación: `5fdf287` | [Revisión humana](../validation/README.md), [pruebas](../../tests/test_human_review.py); [ADR-0026](../adr/0026-human-adjudication-and-effective-model-reporting.md). | Material preparado; veredictos humanos pendientes. | Por asignar. |
| TSK-12 | Publicar ocho páginas y ensayar desde Notion | [Índice local](README.md), [pitch](08-presentacion-al-jurado.md). | Publicación, permisos, registro de ejecución y ensayo pendientes. | Por asignar. |

## 2. Cronología comprobable y reproducción

Los commits anteriores pertenecen al historial local de la rama de trabajo. Su existencia no prueba que estén publicados en GitHub ni que se hayan registrado en Notion durante el evento. Las fechas se obtienen del historial, no de un cronograma supuesto:

```bash
git log --format='%h %aI %s' --date=iso-strict
```

El commit `8b22419` corrige, entre otros, una respuesta de calado que devolvía 45 pies cuando el titular de la prueba contenía 44. La regresión está en `test_canal_answer_quotes_actual_measurement`. Las pruebas de país/año, negación y escape XML también documentan los casos concretos corregidos. Conservar en Notion el fallo reproducido, cambio, ejecución posterior, fecha y responsable real.

La integración de `5fdf287` tiene un registro de verificación local en [ADR-0026](../adr/0026-human-adjudication-and-effective-model-reporting.md). Ese resultado corresponde a esa ejecución; actualizar el estado y número de pruebas con la **última ejecución de `make check`** antes del cierre:

```bash
make check
LLM_PROVIDER=mock DECISION_PROVIDER=mock INGESTION_ENABLED=false make benchmark
```

Guardar las salidas, commit, corpus/manifiesto y entorno. La suite offline no sustituye el ensayo del recorrido completo desde Notion ni una evaluación humana independiente.

## 3. Decisiones técnicas justificadas

1. **Separar reglas de dominio y proveedores.** [ADR-0002](../adr/0002-ports-and-adapters-for-llm-connectors.md) mantiene adaptadores detrás de puertos para poder cambiar proveedor y demostrar el flujo con mocks. El fallback debe identificarse; no acredita desempeño del modelo remoto.
2. **Separar decisión y generación.** [ADR-0010](../adr/0010-system-one-decision-models-cloudflare-clef-and-jev.md) y [ADR-0013](../adr/0013-unified-opencode-routing-for-system-one-and-two.md) describen preguntas tipadas y ruteo. La [ejecución Jev](../validation/decision_jev_2026-10-09.json) compara diez pares sintéticos con regex y guarda salidas; las etiquetas editoriales independientes siguen pendientes.
3. **Distinguir corpus, snapshot y estado operativo.** [ADR-0011](../adr/0011-sqlite-persistent-storage-and-periodic-ingestion.md) y [ADR-0019](../adr/0019-sqlite-offline-snapshot-package.md) separan ingesta/revisiones mutables del paquete de consulta de solo lectura. SQLite permite consultas sin servidor; no crea automáticamente un conjunto de entrenamiento o evaluación independiente.
4. **Responder desde evidencia y mantener revisión humana.** [ADR-0004](../adr/0004-anti-hallucination-and-prompt-injection-defenses.md) y [ADR-0025](../adr/0025-corpus-grounded-query-and-draft-guards.md) aíslan fuentes, devuelven extractos/abstención y validan afirmaciones estructuradas conservadoramente. Los controles no prueban implicación semántica de todos los textos libres.
5. **Proteger la evaluación reservada y registrar el proveedor efectivo.** [ADR-0024](../adr/0024-protect-reserved-benchmark-and-report-real-adapter.md) y [ADR-0026](../adr/0026-human-adjudication-and-effective-model-reporting.md) separan desarrollo, fallbacks y preparación de adjudicación. Las veinte etiquetas expuestas no son ciegas y un archivo externo no prueba independencia por sí solo.
6. **Preparar Notion localmente sin afirmar publicación.** [ADR-0007](../adr/0007-notion-business-contract-and-sync.md) permite carga manual y exige URL, permisos y registros reales. El espejo Markdown no asegura habilitación.
7. **Integrar mediante ramas y revisión.** [ADR-0012](../adr/0012-multi-agent-git-workflow-and-main-protection.md) protege `main`, ligada al despliegue. Los commits locales no equivalen a PR revisada o aplicación desplegada.

## 4. Próximos pasos que requieren personas

Asignar responsables reales; confirmar espacio Business y acceso del jurado; revisar al menos treinta afirmaciones si se producen tantas y los borradores completos; obtener selección editorial independiente y un holdout nuevo bajo custodia; ampliar la evaluación NLP/ML medida a casos editoriales etiquetados; ensayar y registrar el pitch desde Notion. Hasta contar con esas evidencias, los resultados automáticos y el valor operativo se presentan con sus límites.
