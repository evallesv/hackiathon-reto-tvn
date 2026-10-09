# Estado de cumplimiento auditado — 2026-10-09

Este registro compara el repositorio con las secciones 5, 8, 9 y 10 del documento del reto.
Describe evidencias disponibles y tareas pendientes; no asigna una puntuación ni acredita admisión.

| Requisito | Evidencia disponible | Estado y próximo paso |
| :--- | :--- | :--- |
| Demo reproducible offline | Snapshot SQLite de solo lectura; mocks; suite T01–T10 y API. | Comprobado automáticamente. Ensayo completo desde Notion pendiente. |
| Snapshot, diccionario y manifiestos | [Diccionario](DATA_DICTIONARY.md), manifiestos raw/SQLite; `make audit-snapshot`. | Integridad y estructura pasan. 120 noticias dentro de 90 días; cuadrícula de 540 indicadores, 98 valores y 442 nulos. Derechos y calidad editorial requieren revisión por fuente. |
| Consultas sustentadas y abstención | 40 consultas de desarrollo; 20/20 coincidencias literales de valor y fuente; 7/7 abstenciones correctas; 0/20 falsas abstenciones. | Desarrollo controlado. No demuestra sustento semántico de todos los textos. |
| Uso efectivo de IA y baseline | [Diez predicciones reales de Jev](validation/decision_jev_2026-10-09.json): Macro-F1 1.000 frente a regex 0.792; cero fallbacks. | Capacidad de decisión ejecutada. Muestra sintética expuesta; evaluación editorial independiente pendiente. |
| Eficiencia | Jev: mediana 609.280 ms y p95 863.804 ms para esos diez pares. | Tokens y costo sin dato verificado. Ahorro manual frente a asistido no medido. |
| Citas factuales y revisión | Guardas léxicas, IDs/pasajes y [planilla con registros originales](validation/revision_sustento.csv). | T09 parcial. Requiere persona revisora, todas las afirmaciones de respuestas y piezas, y al menos 30 afirmaciones si se producen tantas. Veredictos todavía vacíos. |
| Ranking útil | P@5 exploratorio 0.4 frente a recencia 0.2, relevancia por keywords. | Falta selección independiente de un editor para acreditar utilidad del ranking. |
| Evaluación reservada | Runner admite JSONL nuevo externo; rechaza las etiquetas reservadas expuestas del repositorio. | Faltan autoría/custodia independientes y ejecución del holdout nuevo. La ruta externa no prueba independencia. |
| Cinco fichas, incluida evidencia insuficiente | [Ejemplos locales trazables](notion_spec/05-casos-y-evidencias.md); la fuente adversarial sin titular utilizable bloquea borrador. | Exportar fichas de la ejecución presentada y revisar sus borradores. El JSONL legado contiene nombres/aprobaciones ilustrativos; no usarlo como validación humana. |
| Notion obligatorio | [Ocho páginas preparadas](notion_spec/README.md); pitch de diez minutos conforme al documento. | Falta URL Business, personas responsables, permisos del jurado, registro real y ensayo. Es condición de habilitación. |
| Calidad técnica | Última ejecución local: Ruff, formato y Mypy pasan; 227 pruebas pasan. JavaScript válido; corpus congelado intacto. | Integración mediante PR y revisión humana; no se ha verificado un despliegue nuevo. |

## Información necesaria para cerrar la entrega

1. URL del espacio o página destino de Notion Business y acceso autorizado. Confirmar integrantes y permisos
   del jurado con la organización; registrar fechas y responsables reales.
2. Persona editorial para adjudicar sustento, revisar las cinco fichas y escoger temas relevantes para P@5.
   Registrar correcciones y decisiones efectivas, sin tratar fixtures como aprobaciones.
3. Custodio independiente que prepare consultas nuevas sin exposición durante el ajuste, con el formato
   reservado del runner. Mantener entradas y salidas de ese holdout fuera del repositorio.
4. Evidencia de tokens/costo del proveedor si aplica, y una tarea equivalente manual/asistida para medir
   ahorro de tiempo. Hasta medirlo, el valor operativo permanece como hipótesis.

El snapshot SQLite es corpus consultable offline. El benchmark es un conjunto de preguntas y etiquetas;
no implica que se haya entrenado un modelo supervisado. La separación de desarrollo y evaluación
independiente protege la medición aunque el prototipo use reglas y modelos preentrenados.
