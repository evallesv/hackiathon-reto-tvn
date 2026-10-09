# ADR-0018: Evidencia viva compartida por consultas, agenda y fichas

- **Estado**: Aceptado
- **Fecha**: 2026-10-08
- **Contexto**: La ingesta viva ya alimenta la agenda, pero las consultas aún respondían solo desde el snapshot y la vista de fichas solo mostraba registros persistidos. Esto podía mostrar evidencia distinta según la pantalla y perder las marcas de revisión al regenerar una ficha viva.

## Decisión

Las consultas editoriales consultan primero noticias vivas dentro de la ventana configurada y conservan noticias congeladas para búsquedas históricas. Indicadores y eventos USGS vivos se combinan con sus registros congelados por claves naturales (país/serie/año para indicadores, ID para eventos), dando precedencia al registro vivo cuando ambas capas describen el mismo dato.

La vista de fichas combina los casos persistidos y la agenda viva actual. Los IDs de caso vivo permanecen estables a partir de la clave de agrupación del titular. Al recalcular una agenda, el servicio restaura borrador, estado de revisión, revisor y observaciones de los casos vivos previamente guardados. Un caso vivo se persiste cuando se registra una revisión humana; el acceso de lectura no escribe la base de datos.

El benchmark y las pruebas permanecen aislados del contenido vivo. El snapshot se mantiene como archivo de referencia para reproducibilidad y como respaldo histórico.

## Consecuencias

- Agenda, consulta, detalle y revisión pueden trabajar sobre el mismo registro vivo y usar sus IDs y enlaces como citas.
- La capa congelada sigue disponible para preguntas históricas y para abstenerse cuando ninguna fuente sustenta la consulta.
- Las fichas actuales se combinan en memoria con las persistidas; el GET no materializa automáticamente todos los titulares como casos revisables.
- El contenido de noticia continúa sujeto al alcance que entregue el feed, que puede limitarse a titular y metadatos.
