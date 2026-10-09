# Contenido local para Notion Business

Este directorio prepara las ocho páginas exigidas por la sección 5 del reto. **La publicación en Notion y la verificación del acceso del jurado están pendientes.** Tener estos archivos en GitHub no acredita la habilitación para evaluación.

Notion debe ser el registro del trabajo y la superficie de presentación. La carga manual es válida; no se exige Notion AI ni sincronización automática. El espacio debe compartirse con participantes y jurado autorizados, sin necesidad de publicarlo en la web.

## Páginas preparadas

| # | Página | Contenido local | Estado en Notion |
| :--- | :--- | :--- | :--- |
| 01 | [Inicio del reto](01-inicio-del-reto.md) | Usuario, modalidad, alcance, criterios de éxito y enlaces. | Publicación y accesos pendientes. |
| 02 | [Plan y decisiones](02-plan-y-decisiones.md) | Backlog y decisiones; completar responsables reales y enlaces a evidencias de ejecución. | Publicación y registro de trabajo pendientes. |
| 03 | [Catálogo de datos](03-catalogo-de-datos.md) | Fuentes, contratos, condiciones, períodos y referencia a manifiestos. | Publicación y verificación del catálogo pendientes. |
| 04 | [Diseño de solución](04-diseno-de-solucion.md) | Arquitectura, contratos, reglas, modelos, prompts y limitaciones. | Publicación y revisión de configuración final pendientes. |
| 05 | [Casos y evidencias](05-casos-y-evidencias.md) | Cinco fixtures ilustrativos; exportar fichas actuales y registrar revisiones humanas reales. | Publicación y revisión humana pendientes. |
| 06 | [Pruebas y métricas](06-pruebas-y-metricas.md) | Matriz T01–T10 y resultados exploratorios; adjuntar salida de la ejecución final y correcciones. | Publicación y evidencia final pendientes. |
| 07 | [Riesgos y ética](07-riesgos-y-etica.md) | Riesgos, derechos, controles y límites. | Publicación y revisión pendientes. |
| 08 | [Presentación al jurado](08-presentacion-al-jurado.md) | Recorrido de diez minutos desde Notion, con enlaces al prototipo. | Publicación, accesos y ensayo pendientes. |

## Carga y verificación antes del cierre

1. Confirmar con la organización los puestos o invitados de Business y los permisos de participantes y jurado. Registrar la URL del espacio y quién verificó el acceso.
2. Importar o copiar las ocho páginas. Completar responsables, fechas y evidencias reales de tareas y decisiones durante la ejecución; no inventar retrospectivamente revisiones o una cronología en Notion.
3. Incorporar el catálogo del paquete utilizado y al menos cinco fichas trazables, incluyendo una con evidencia insuficiente. Los nombres y aprobaciones de fixtures no cuentan como revisiones reales.
4. Ejecutar `make check` y el benchmark correspondiente; guardar su salida final, entorno, fecha, numeradores, denominadores y fallos. Mostrar al menos una prueba fallida y su corrección verificable.
5. Adjuntar los manifiestos y hashes del corpus de evaluación y del snapshot de demostración, identificando cuál se usó en cada ejecución.
6. Ensayar el pitch desde esta página de Notion, abrir los enlaces al prototipo y comprobar el recorrido sin internet. Registrar el ensayo y verificar el acceso al repositorio.

El resultado y el número de pruebas se toman de la **última ejecución de `make check`**. Un espejo Markdown, una suite verde o un PDF de respaldo no sustituyen la URL accesible, el registro y la presentación obligatorios en Notion.
