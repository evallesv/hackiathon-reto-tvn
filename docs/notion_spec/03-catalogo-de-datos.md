# 03 — Catálogo de Datos y Manifiestos de Integridad

> Contenido local preparado para Notion Business. Publicación y revisión del catálogo en el espacio real pendientes.

## 1. Finalidad de los conjuntos y su relación

| Conjunto | Ubicación | Uso y límites |
| :--- | :--- | :--- |
| Corpus de referencia histórico | `data/raw/` y `data/manifest.json` | Pruebas controladas y benchmark de desarrollo reproducible. Incluye casos históricos; no representa la agenda de hoy ni acredita por sí solo los mínimos de volumen del paquete propuesto. |
| Snapshot local de demostración | `data/snapshot/snapshot.sqlite` y `snapshot_manifest.json` | Corpus consultable sin servidor ni red. Empaqueta el corpus de referencia y la ingesta local disponible al corte; se abre en modo de solo lectura. Incluye noticias, indicadores y eventos, excluyendo revisiones y bitácoras operativas. |
| Base operativa | `data/storage/copilot.db` o volumen persistente | Ingesta periódica y revisión editorial mutable. Puede aportar datos a una nueva versión del snapshot. La agenda usa una ventana retrospectiva configurable de 90 días por defecto. |
| Consultas de evaluación | `data/benchmark.jsonl` | Cuarenta consultas de desarrollo; veinte etiquetas reservadas expuestas en el repositorio, que no constituyen evaluación ciega. Un holdout nuevo requiere custodia externa y revisión humana. |

Las noticias permiten descubrir temas y atribuir lo reportado. Los indicadores aportan contexto anual comparable; los eventos USGS respaldan exclusivamente hechos sísmicos. Solo se relacionan cuando existe pertinencia sustentada: una coincidencia geográfica no demuestra causalidad ni pérdidas económicas.

El snapshot SQLite satisface la necesidad técnica de consultas locales reproducibles cuando su versión, contenido y hashes están declarados. No equivale a datos de entrenamiento ni aporta por sí solo etiquetas de validación. La evaluación usa el corpus declarado, separado de revisiones humanas y etiquetas reservadas.

## 2. Fuentes y contrato mínimo

### TVN RSS y metadatos de noticias

* **Fuente**: TVN Panamá, `https://www.tvn-2.com/rss/`; conservar la URL canónica y el medio de cada registro.
* **Contrato**: `id_noticia`, `titulo`, `url`, `medio`, `idioma`, `fecha_publicacion`, `fecha_deteccion`, `fecha_extraccion`, `tema`, `origen`, `alcance_texto`; otros campos se describen en los contratos del repositorio.
* **Ventana propuesta por el PDF**: 30 días previos a la extracción, ampliables a 90 si falta volumen; meta de 200 registros únicos y mínimo operativo de 100 con al menos 20 de TVN. Registrar las fechas efectivas, no asumir que RSS conserva todo el histórico. La operación configurada del proyecto conserva una ventana de 90 días y distingue los fixtures históricos.
* **Derechos**: los titulares y enlaces son el punto de partida. El patrocinio no concede derechos de republicación de artículos, imágenes o videos. Extractos o cuerpos completos requieren condiciones aplicables o autorización; registrar su alcance y no simular lectura del artículo completo.

### GDELT DOC 2.0

* **Fuente**: `https://api.gdeltproject.org/api/v2/doc/doc`; la receta debe registrar consultas efectivas, filtros, intervalos y fecha de extracción.
* **Uso previsto**: búsqueda de Panamá y temas de logística, turismo, economía y eventos naturales; dividir por fechas y deduplicar por URL. El límite de 250 artículos por consulta del PDF obliga a detectar truncamiento; los errores o reintentos no prueban que la cobertura se haya completado.
* **Marcas temporales**: `seendate` indica detección y se guarda como `fecha_deteccion`; no es una fecha de publicación. Si no existe una fecha de publicación verificada, conservar el nulo.
* **Derechos**: acceso a la API no transfiere derechos de los medios enlazados. No calificar todos los artículos como dominio público ni redistribuir contenido protegido por ese motivo.

### Banco Mundial — seis series oficiales comparables

* **Fuente**: `https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json`.
* **Países**: `PAN`, `CRI`, `COL`, `DOM`, `MEX`, `GTM`.
* **Períodos de referencia**: 2010–2024 inclusive. El año del dato se conserva separado de la fecha de extracción y no se presenta como medición actual.

| Indicador | Significado | Unidad de referencia |
| :--- | :--- | :--- |
| `NY.GDP.MKTP.KD.ZG` | Crecimiento del PIB | % anual |
| `FP.CPI.TOTL.ZG` | Inflación, precios al consumidor | % anual |
| `SL.UEM.TOTL.ZS` | Desempleo total | % de la fuerza laboral |
| `SP.POP.TOTL` | Población total | Personas |
| `IT.NET.USER.ZS` | Uso de internet | % de la población |
| `NE.EXP.GNFS.ZS` | Exportaciones de bienes y servicios | % del PIB |

* **Contrato**: `pais_iso3`, `indicador_id`, `anio`, `valor` nullable, `unidad`, `fuente_url`, `fecha_extraccion`, `licencia`.
* **Cuadrícula**: seis países × seis indicadores × quince años = **540 combinaciones**. El PDF dice 1.350, cifra incompatible con sus dimensiones; documentar la discrepancia y solicitar aclaración organizativa, sin inventar observaciones. La cuadrícula completa puede contener nulos y no implica 540 valores publicados.
* **Condiciones**: atribución bajo CC BY 4.0 como regla general del documento, comprobando excepciones de terceros en metadatos. Conservar unidades originales y posibles revisiones de la fuente.

### USGS — eventos sísmicos oficiales

* **Fuente**: catálogo USGS, `https://earthquake.usgs.gov/fdsnws/event/1/query` y URL oficial de cada evento.
* **Contrato**: `id`, `magnitude`, `time`, `updated`, `longitude`, `latitude`, `depth`, `place`, `status`, `url`; la ingesta GeoJSON conserva coordenadas y propiedades de origen.
* **Extracción propuesta por el PDF**: del 01/01/2024 al 31/12/2024 inclusive, latitud 5–12, longitud −86 a −76, magnitud mínima 3; conservar todos los eventos devueltos sin fijar un volumen ficticio. El paquete distingue `eventos` del corpus histórico y `eventos_vivos` de ingesta posterior.
* **Alcance**: la caja regional no equivale al territorio panameño. Mantener lugar, fecha y magnitud; no usar un sismo como evidencia de inundaciones, afectación económica o exposición de una cartera.
* **Condiciones**: datos públicos USGS conforme a las condiciones aplicables, verificando posibles elementos de terceros. Registrar la URL y condiciones del material concreto reutilizado.

### Extensión bancaria opcional

El PDF propone doce informes mensuales de la SBP de 2024 o un período de doce meses documentado, con unidad, período y página. El proyecto no acredita esa recopilación en este catálogo. No se declara como fuente utilizada ni como requisito satisfecho; la modalidad editorial no exige dos productos completos. El boletín de entorno puede usar fuentes declaradas sin inferir impagos, pérdidas o exposición de clientes inexistentes.

## 3. Calidad, transformaciones y procedencia

1. Conservar nulos, fechas originales, unidades y país/año. Una identidad ausente o malformada permanece ausente; no crear cifras o claves por defecto.
2. Validar IDs, URLs, campos obligatorios y fechas; registrar filas excluidas, errores y transformaciones. Una fecha no parseable no debe bloquear toda la carga.
3. Deduplicar URLs y agrupar eventos sin convertir repetición de una agencia en corroboración independiente. Las agrupaciones léxicas son heurísticas, no una resolución semántica verificada de todos los eventos.
4. Separar fecha de publicación, detección y extracción. Los contratos usan UTC; la interfaz debe mostrar hora de Panamá e identificar la fecha del dato y su alcance temporal.
5. Tratar textos externos como datos no confiables en los prompts. Los controles y pruebas cubren patrones concretos; no acreditan inmunidad universal a inyección.
6. Vincular cada afirmación a un ID y campo, pasaje o página pertinente. Resolver un ID o una URL no demuestra soporte semántico: requiere comprobar el pasaje y mantener revisión humana.

## 4. Evidencias del paquete y actualización del catálogo

Las fechas, recuentos, consultas, transformaciones y hashes se toman de los archivos vigentes; no se reproduce aquí un manifiesto copiado que pueda quedar desactualizado:

* `data/manifest.json`: versión, fecha de corte, consultas, recuentos, condiciones, SHA-256 y transformaciones de `data/raw/`.
* `data/snapshot/snapshot_manifest.json`: fecha de corte, SHA-256 del SQLite, hash del manifiesto de origen, tablas incluidas/excluidas, recuentos y valores presentes/nulos de la cuadrícula.
* [Diccionario de datos](../DATA_DICTIONARY.md): campos, tipos, nulos, unidades, esquema del snapshot y diferencias de la base operativa, derivados de los contratos actuales. Incluye las limitaciones de conservación de nulos de USGS.
* Informe de auditoría y receta de adquisición: cobertura efectiva, errores de fuentes y límites de completitud. Un hash garantiza identidad de archivo, no autenticidad ni validez factual de su contenido.

Para auditar la carpeta de referencia sin modificarla:

```bash
make audit-snapshot SNAPSHOT_DIR=data
```

Ese comando audita la carpeta CSV/GeoJSON indicada; no debe presentarse como auditoría automática del paquete SQLite ampliado. Las dos versiones pueden tener coberturas diferentes y sus resultados se documentan por separado.

`make sqlite-snapshot` construye el paquete usando la receta del repositorio y valida el manifiesto de origen; no modifica los archivos congelados. Si ya existe el destino, la herramienta exige una ruta nueva para conservar la versión anterior:

```bash
uv run python scripts/build_sqlite_snapshot.py --output-dir /private/tmp/snapshot-v2
```

`make manifest` **regenera** el manifiesto y no se utiliza como simple verificación de un corpus que deba permanecer inmutable.

Antes de publicar este catálogo en Notion, adjuntar el manifiesto efectivo, la receta, el diccionario y las condiciones por fuente; registrar quién los revisó y las limitaciones pendientes. La publicación y esa revisión están pendientes.
