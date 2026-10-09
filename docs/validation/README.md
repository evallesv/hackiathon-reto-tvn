# Revisión humana del sustento

La planilla `revision_sustento.csv` contiene unidades de respuesta del benchmark de desarrollo y registros
originales del corpus histórico. No contiene veredictos, revisores ni aprobaciones. No acredita validación
independiente ni reemplaza la revisión de borradores editoriales completos.

1. Asignar una persona revisora real. Abrir el registro original y comprobar campo, fecha, país, unidad
   y alcance del pasaje, además de la URL cuando sea pertinente.
2. Identificar cada afirmación factual emitida en `respuesta_completa`. Copiar la fila por cada afirmación
   adicional; asignar un `id_afirmacion_revisada` único y registrar su texto y tipo. Una respuesta puede
   contener varias afirmaciones; veinte respuestas no equivalen a veinte ni a treinta afirmaciones.
3. Marcar `sustento_valido_si_no` como `si` solo si una evidencia identificable respalda ese enunciado
   concreto. Registrar `no` y explicar detalles ausentes, cifras/períodos distintos, negaciones, atribución
   o causalidades no sustentadas. Un ID existente no basta para aprobar la afirmación.
4. Añadir persona, fecha UTC y observaciones. Las filas sin afirmación o sin veredicto permanecen pendientes.
   Examinar también los hechos de brief/copy/guion y boletín bancario cuando se generen; incorporar sus
   afirmaciones y pasajes a la misma revisión. Los fixtures con nombres o aprobaciones ficticias no sirven
   como evidencia de revisión humana.
5. Informar afirmaciones válidas / afirmaciones revisadas, porcentaje y lista de fallos. Revisar al menos
   treinta afirmaciones si se producen tantas, según sección 9.1; declarar el tamaño disponible si son menos.
   No contar inferencias/hipótesis como hechos ni asumir aprobadas las afirmaciones pendientes.

Para preparar otra versión sin sobrescribir la actual:

```bash
LLM_PROVIDER=mock DECISION_PROVIDER=mock INGESTION_ENABLED=false make benchmark
uv run python scripts/prepare_human_review.py --output /private/tmp/revision-sustento-v2.csv
```

El exportador admite solo desarrollo. El custodio mantiene las evaluaciones reservadas y sus reportes
fuera del repositorio. Un archivo externo no prueba por sí mismo independencia: debe registrarse autoría,
custodia y ausencia de exposición durante los ajustes.
