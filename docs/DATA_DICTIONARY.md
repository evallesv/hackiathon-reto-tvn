# Diccionario de datos del corpus y del snapshot SQLite

Este documento describe los contratos y esquemas implementados. Complementa el [catálogo de fuentes](notion_spec/03-catalogo-de-datos.md); las fechas de corte, cantidades, hashes y condiciones efectivas se consultan en los manifiestos del paquete utilizado.

Fuentes del diccionario: [modelos](../src/hackiathon_reto_tvn/domain/models.py), [carga de CSV/GeoJSON](../src/hackiathon_reto_tvn/adapters/data/loaders.py), [dimensiones de indicadores](../src/hackiathon_reto_tvn/domain/snapshot_contract.py), [snapshot SQLite](../src/hackiathon_reto_tvn/adapters/data/sqlite_snapshot.py) y [base operativa](../src/hackiathon_reto_tvn/adapters/data/sqlite_storage.py).

## Convenciones y lectura de nulos

* Los archivos de intercambio usan UTF-8. CSV representa los datos de noticias e indicadores; GeoJSON representa las features de USGS.
* `str`, `int` y `float` son tipos del contrato Python; `TEXT`, `INTEGER` y `REAL` son sus tipos en el snapshot SQLite. «Nullable» indica que el modelo permite `None` y el snapshot permite `NULL`.
* Un texto vacío `""` no es un `NULL`. Los modelos de noticias y eventos no admiten nulos; esto no implica que sus cadenas sean completas o válidas.
* Las fechas de noticias y extracción son cadenas cuya convención es ISO 8601 UTC. El modelo `str` no valida por sí solo esa convención. Los tiempos de USGS son enteros Unix en milisegundos, separados de la fecha de extracción del paquete.
* Una URL o un ID presente no acredita pertinencia factual. Las afirmaciones deben citar además el campo o pasaje y su alcance; la revisión humana comprueba sustento.

## Noticias: `noticias.csv` → `Noticia` → tabla `noticias`

| Campo | Tipo Python / SQLite | Nullable | Significado y unidad |
| :--- | :--- | :--- | :--- |
| `id_noticia` | `str` / `TEXT` | No | Identificador de registro; clave primaria en el snapshot. Sin unidad. |
| `titulo` | `str` / `TEXT` | No | Titular de la fuente. El loader omite filas sin título utilizable. |
| `url` | `str` / `TEXT` | No | Enlace de origen; se usa para fusionar/deduplicar noticias al empaquetar. No es un tipo URL validado en el modelo. |
| `medio` | `str` / `TEXT` | No | Nombre del medio; no prueba independencia editorial o procedencia primaria. |
| `idioma` | `str` / `TEXT` | No | Código de idioma en texto; valor predeterminado del modelo: `es`. |
| `fecha_publicacion` | `str` / `TEXT` | No | Fecha declarada de publicación. Puede quedar vacía o conservar una cadena malformada en la carga histórica. |
| `fecha_deteccion` | `str` / `TEXT` | No | Fecha en que se detectó el registro; `seendate` de GDELT corresponde a este campo. |
| `fecha_extraccion` | `str` / `TEXT` | No | Fecha de extracción registrada para la fila. |
| `tema` | `str` / `TEXT` | No | Etiqueta temática; el contrato no la restringe mediante enum. |
| `origen` | `str` / `TEXT` | No | Procedencia técnica del registro; distinta del nombre del medio. |
| `alcance_texto` | `str` / `TEXT` | No | Alcance disponible; predeterminado `titular_metadatos`. Es texto libre en el modelo. |

El loader histórico conserva las fechas como texto. Sus parsers auxiliares pueden devolver `None` cuando no son interpretables; eso no convierte la columna de `Noticia` en nullable. Las cadenas faltantes reciben vacíos o valores por defecto según el campo. Un ID ausente puede recibir `noticia_<índice>`: no debe describirse esa identidad de reparación como un ID estable verificado por la fuente.

El snapshot contiene únicamente estos once campos. `resumen` y `metadata_json` existen en la base operativa, pero no forman parte de `Noticia` ni de la tabla `noticias` empaquetada. Disponer de un enlace o un resumen operativo no demuestra que el artículo completo haya sido leído.

## Indicadores: `indicadores.csv` → `Indicador` → tabla `indicadores`

| Campo | Tipo Python / SQLite | Nullable | Significado y unidad |
| :--- | :--- | :--- | :--- |
| `pais_iso3` | `str \| None` / `TEXT` | Sí | País identificado por código ISO3; ausencia permanece nula. |
| `indicador_id` | `str \| None` / `TEXT` | Sí | Código oficial de la serie; ausencia permanece nula. |
| `anio` | `int \| None` / `INTEGER` | Sí | Año de referencia, no año de extracción. Valores ausentes o no enteros quedan nulos en la carga. |
| `valor` | `float \| None` / `REAL` | Sí | Observación de la serie en su unidad. Un nulo no significa cero ni observación publicada. |
| `unidad` | `str` / `TEXT` | No | Unidad original de la observación o unidad de referencia de una fila de cuadrícula sin valor. |
| `fuente_url` | `str` / `TEXT` | No | URL de la serie o consulta correspondiente; texto sin validación URL automática. |
| `fecha_extraccion` | `str` / `TEXT` | No | Fecha registrada de extracción; para filas añadidas sin observación, fecha de construcción de la cuadrícula. |
| `licencia` | `str` / `TEXT` | No | Condiciones registradas; predeterminado del modelo `CC BY 4.0`. No sustituye revisar excepciones de la fuente. |

La clave compuesta es `(pais_iso3, indicador_id, anio)`. El esquema del snapshot permite nulos en esas columnas; una fila sin identidad completa no es una combinación válida para comprobar cobertura. La base operativa tiene restricciones diferentes, descritas más abajo.

Las dimensiones de referencia son `PAN`, `CRI`, `COL`, `DOM`, `MEX`, `GTM`, años 2010–2024 inclusive y las seis series siguientes:

| `indicador_id` | Concepto | Unidad de referencia para completar la cuadrícula |
| :--- | :--- | :--- |
| `NY.GDP.MKTP.KD.ZG` | Crecimiento del PIB | `% anual` |
| `FP.CPI.TOTL.ZG` | Inflación | `% anual` |
| `SL.UEM.TOTL.ZS` | Desempleo total | `% de fuerza laboral` |
| `SP.POP.TOTL` | Población total | `personas` |
| `IT.NET.USER.ZS` | Uso de internet | `% de población` |
| `NE.EXP.GNFS.ZS` | Exportaciones de bienes y servicios | `% del PIB` |

Los valores existentes conservan su unidad original, que puede usar una abreviatura distinta. La cuadrícula esperada tiene 540 combinaciones; el constructor añade las ausentes con `valor=None`, URL de consulta, unidad de referencia y fecha de empaquetado. Esa fila documenta ausencia en el contenido disponible: no acredita que se haya descargado una observación ni que la fuente carezca de ella. El manifiesto distingue valores presentes y nulos.

## USGS: `eventos.geojson` → `EventoGeoJSON` → `eventos` / `eventos_vivos`

| Campo normalizado | Ubicación en GeoJSON | Tipo Python / SQLite | Nullable | Significado y unidad |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `feature.id` | `str` / `TEXT` | No | Identificador oficial del evento; clave primaria. |
| `magnitude` | `properties.mag` | `float` / `REAL` | No | Magnitud informada. El contrato no conserva `magType`, por lo que no permite afirmar una escala específica para todos los eventos. |
| `time` | `properties.time` | `int` / `INTEGER` | No | Tiempo del evento, milisegundos Unix UTC. |
| `updated` | `properties.updated` | `int` / `INTEGER` | No | Última actualización informada, milisegundos Unix UTC. |
| `longitude` | `geometry.coordinates[0]` | `float` / `REAL` | No | Longitud en grados. |
| `latitude` | `geometry.coordinates[1]` | `float` / `REAL` | No | Latitud en grados. |
| `depth` | `geometry.coordinates[2]` | `float` / `REAL` | No | Profundidad en kilómetros. |
| `place` | `properties.place` | `str` / `TEXT` | No | Descripción de ubicación de la fuente; la caja consultada no equivale al territorio panameño. |
| `status` | `properties.status` | `str` / `TEXT` | No | Estado informado por USGS; distinto de `estado_revision` editorial. |
| `url` | `properties.url` | `str` / `TEXT` | No | URL oficial del evento; texto sin validación URL automática. |

El contrato mantiene nombres ingleses de USGS en snake_case. No incorpora intensidad, daños, fallecimientos, impacto económico ni una fecha propia de extracción por evento.

### Límite actual de conservación de nulos USGS

La conservación de nulos de indicadores **no se extiende íntegramente a USGS**:

* `EventoGeoJSON` exige los campos numéricos. El loader histórico excluye una feature si falta magnitud, tiempo, actualización o cualquiera de las tres coordenadas, o si su valor no admite el contrato. Registra un diagnóstico con el índice, ID y error; continúa cargando las demás features. No sustituye valores ausentes por cero ni modifica el GeoJSON de origen.
* En `eventos_live`, `updated` y coordenadas pueden ser `NULL`. El empaquetado valida las observaciones almacenadas sin imputación: un nulo incompatible con `EventoGeoJSON`, incluso en sus campos de texto, hace fallar la creación con un error que identifica el evento. El snapshot no se publica parcialmente; hay que corregir el registro desde una fuente verificable o ampliar deliberadamente el contrato.
* Los ceros presentes en el GeoJSON o almacenados en la base operativa siguen siendo valores válidos y se conservan al cargar o empaquetar. Esto no prueba que toda ruta de ingesta anterior preserve los nulos ni valida la calidad geográfica de la fuente.

Los eventos parciales no se representan como modelos con `null`: admitirlos y conservarlos en las consultas requiere ampliar el contrato compartido, sus tablas y pruebas. La exclusión con diagnóstico y el rechazo del paquete incompleto evitan fabricar mediciones mientras esa ampliación permanece pendiente.

## Tablas del snapshot portátil

| Tabla | Contenido | Clave / tipos | Alcance |
| :--- | :--- | :--- | :--- |
| `noticias` | Los once campos de `Noticia` | `id_noticia`; tipos descritos arriba | Fusiona corpus histórico y noticias operativas incluidas al corte por URL; la fila operativa prevalece si comparte URL. |
| `indicadores` | Los ocho campos de `Indicador` | `(pais_iso3, indicador_id, anio)` | Fusiona series por identidad; una fila operativa prevalece ante la misma clave. Añade combinaciones ausentes con valor nulo. |
| `eventos` | Los diez campos de `EventoGeoJSON` | `id` | Features cargadas desde el GeoJSON de referencia. El período propuesto del reto es 2024; verificar cobertura real en la auditoría. |
| `eventos_vivos` | Mismo esquema de `eventos` | `id` | Eventos disponibles en la base operativa al empaquetar, separados de las features históricas. Su inclusión no prueba cumplimiento del período histórico ni descarga completa. |
| `snapshot_metadata` | Metadatos del paquete | `clave TEXT PRIMARY KEY`, `valor_json TEXT NOT NULL` | Valores JSON de versión, fechas, hashes y recuentos. |

Las columnas de noticias/eventos salvo sus claves primarias están declaradas `NOT NULL` en el snapshot. Las claves primarias de texto no tienen `NOT NULL` explícito en el SQL; los modelos exigen cadenas al construir/leer el paquete. No confundir esa validación de aplicación con una restricción SQL adicional.

`load_eventos()` combina las dos tablas por ID para consulta, con preferencia del registro vivo ante el mismo ID. Un auditor que necesite comprobar el período histórico debe examinar `eventos` por separado; el resultado combinado no conserva una etiqueta de tabla en `EventoGeoJSON`.

Las claves actuales de `snapshot_metadata` son:

| Clave | Tipo del valor JSON | Significado |
| :--- | :--- | :--- |
| `schema_version` | Entero | Versión del esquema del paquete. |
| `fecha_corte_utc` | Cadena | Fecha UTC de construcción del snapshot. |
| `source_manifest_cutoff_utc` | Cadena | Fecha de corte declarada en el manifiesto de referencia. |
| `source_manifest_sha256` | Cadena | SHA-256 del manifiesto de referencia usado. |
| `source_live_content_sha256` | Cadena | Hash del contenido operativo seleccionado para empaquetar. |
| `source_live_content_counts` | Objeto de enteros | Cantidades de noticias, indicadores y eventos operativos seleccionados. |
| `counts` | Objeto de enteros | Cantidades finales por conjunto empaquetado. |
| `indicator_grid` | Objeto | Combinaciones esperadas, valores presentes, valores nulos y declaración de ausencia sin imputar valores. |

El archivo acompañante `snapshot_manifest.json` agrega nombre y SHA-256 del SQLite, tablas incluidas/excluidas y si se incorporó ingesta operativa. La versión se identifica con ese manifiesto; un hash prueba identidad del contenido, no sustento de sus afirmaciones.

## Diferencias de la base operativa mutable

La base operativa `copilot.db` usa WAL y conserva ingesta y revisiones. Sus tablas no son idénticas al paquete de lectura:

| Tabla operativa | Diferencias relevantes respecto al corpus |
| :--- | :--- |
| `noticias_live` | Añade `resumen TEXT`, `metadata_json TEXT` y `created_at TEXT NOT NULL`. `url` es único. Varias cadenas del corpus admiten `NULL` en SQL; no se debe asumir que eso las hace válidas para el modelo `Noticia`. |
| `indicadores_live` | Añade `id INTEGER PRIMARY KEY AUTOINCREMENT` y `created_at TEXT NOT NULL`. País, indicador y año son `NOT NULL`, con clave única compuesta; `valor` es nullable. Unidad, URL, extracción y licencia admiten nulos en SQL, a diferencia del snapshot. |
| `eventos_live` | Usa `longitud`, `latitud` y `profundidad` para las coordenadas; añade `created_at TEXT NOT NULL`. `updated`, URL, coordenadas y estado admiten `NULL`; magnitud, lugar y tiempo son `NOT NULL`. La conversión al contrato se describe en el límite USGS. |
| `ingestion_runs` | Guarda fuente, estado, cantidad, detalles, inicio y fin de cada ejecución. Es bitácora operativa; no se incluye en el snapshot. |
| `fichas_casos` | Guarda score, evidencia, estado editorial, persona revisora, notas y `ficha_json`, con fechas de creación/actualización. Es estado de trabajo; no se incluye en el snapshot del corpus. |

Los campos operativos `created_at` y `updated_at` son cadenas de fecha UTC generadas por el adaptador. No sustituyen fecha de publicación, período anual del indicador o tiempo del sismo. Un estado de USGS tampoco equivale a aprobación humana de un borrador.

Consultar una copia SQLite local no necesita un servidor de base de datos. Para una demostración reproducible se fija el corpus mediante el snapshot de solo lectura y se mantiene aparte la base operativa que recibe nuevas revisiones e ingesta. Entrenamiento, etiquetas de desarrollo y validación independiente son decisiones adicionales; no se deducen de ese formato de almacenamiento.
