# ADR-0007: Preparación local y registro obligatorio en Notion Business

* **Estado**: Aceptado; publicación y verificación de acceso en Notion pendientes
* **Fecha inicial**: 2026-10-06
* **Revisión**: 2026-10-09
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

La sección 5 del documento del reto exige Notion Business como registro de ejecución y superficie oficial de presentación. Para ser admitida, la entrega necesita una URL accesible al jurado, al menos ocho tareas y tres decisiones justificadas, un catálogo completo, cinco fichas trazables con un caso de evidencia insuficiente, pruebas T01–T10 con métricas finales y un pitch de diez minutos desde Notion.

La organización debe confirmar puestos o invitados, permisos y acceso del jurado. La licencia no presupone cuentas ilimitadas ni cubre servicios externos de IA. No se exige Notion AI ni automatizar la carga. Un repositorio, PDF o PowerPoint no reemplaza el espacio.

## Decisión

1. Mantener `docs/notion_spec/` como contenido local versionado para preparar las ocho páginas: Inicio del reto, Plan y decisiones, Catálogo de datos, Diseño de solución, Casos y evidencias, Pruebas y métricas, Riesgos y ética y Presentación al jurado.
2. Permitir importar o copiar manualmente ese contenido. La exportación JSON de fichas sirve como insumo; requiere mapear campos a las páginas o bases de Notion. No se afirma que exista una sincronización automática ni una exportación de bloques de Notion implementada.
3. Completar en Notion los responsables reales, fechas, decisiones, pruebas fallidas, correcciones y revisión humana durante la ejecución. Las fichas y nombres de fixtures ilustrativos no acreditan decisiones de personas reales.
4. Compartir el espacio con participantes y jurado autorizados. Registrar su URL y comprobar permisos antes del cierre; no publicar secretos ni exigir acceso público en la web.
5. Incorporar resultados de la última ejecución de `make check`, benchmark, entorno, proveedor efectivo y limitaciones. Distinguir corpus de evaluación y snapshot de demostración mediante sus manifiestos.
6. Presentar desde Notion el pitch y el recorrido del prototipo mediante enlaces o embeds. Guardar evidencia del ensayo offline y de acceso al repositorio.

## Consecuencias

El espejo local facilita revisión, reproducibilidad y preparación de una carga manual. **No asegura la habilitación del equipo ni prueba que Notion se haya utilizado durante el evento.** La publicación, los permisos, la documentación de ejecución y el pitch deben comprobarse en el espacio real.

La integración automatizada es opcional y puede incorporarse después si existe acceso autorizado. Hasta entonces, el estado del entregable es «contenido local preparado; publicación y acceso en Notion pendientes».
