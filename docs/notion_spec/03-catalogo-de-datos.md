# 03 — Catálogo de Datos y Manifiesto de Integridad

> **Espacio Oficial de Presentación en Notion Business**  
> **Catálogo de Fuentes, Esquemas, Licencias y Manifiesto Criptográfico SHA-256**

---

## 1. Visión General de las Fuentes de Datos

El sistema integra 4 orígenes de información heterogéneos, categorizados en dos capas operativas:
1. **Capa Benchmark / Snapshot Congelado**: Almacenada en `data/raw/` y sellada criptográficamente en `data/manifest.json` para garantizar reproducibilidad exacta al 100%.
2. **Capa de Ingesta Continua (Live Feeds)**: Almacenada en SQLite WAL (`copilot.db`), con conectores programados para actualización periódica.

---

## 2. Catálogo Detallado de Fuentes

### 2.1. Fuente 1: TVN RSS Panamá (Noticias Nacionales)
- **Tipo de Origen**: Feed XML RSS público de medios informativos nacionales.
- **Endpoint / URL Base**: `https://www.tvn-2.com/rss/` y sitios aliados de prensa.
- **Formato**: CSV tabular normalizado (`noticias.csv`).
- **Cobertura Temporal**: Eventos noticiosos de 2022 a 2024 (incluye deliberadamente noticias históricas para verificar el detector de recirculación T03).
- **Cobertura Geográfica**: República de Panamá (Ciudad de Panamá, Provincias Centrales, Canal de Panamá).
- **Esquema de Campos**:
  - `id_noticia` (`TEXT`): Identificador único (e.g. `NOT-001`).
  - `titulo` (`TEXT`): Titular periodístico.
  - `url` (`TEXT`): Enlace canónico de la fuente.
  - `medio` (`TEXT`): Nombre del medio emisor (TVN Noticias, Panamá América, La Estrella).
  - `idioma` (`TEXT`): Código ISO `es`.
  - `fecha_publicacion` (`TEXT ISO8601`): Fecha oficial declarada de emisión.
  - `fecha_deteccion` (`TEXT ISO8601`): Marca temporal de captura en el sistema.
  - **GDELT**: `seendate` se conserva como `fecha_deteccion`; no se usa como fecha de publicación. Si no se verifica por separado, `fecha_publicacion` queda vacía.
  - `fecha_extraccion` (`TEXT ISO8601`): Fecha de procesamiento por el loader.
  - `tema` (`TEXT`): Categoría temática (`infraestructura`, `logistica`, `salud`, `clima`).
  - `origen` (`TEXT`): Origen técnico (`tvn_rss`, `gdelt`, etc.).
  - `alcance_texto` (`TEXT`): `titular_metadatos` o `cuerpo_completo`.
  - `resumen` (`TEXT`): Extracto informativo.
  - `metadata` (`JSON`): Metadatos adicionales (entidades, tags).
- **Licencia y Términos**: Derechos de autor reservados TVN / Medios panameños. Uso referencial exclusivo para investigación y evaluación en el marco del HackIAthon.

### 2.2. Fuente 2: GDELT DOC 2.0 (Global Database of Events, Language, and Tone)
- **Tipo de Origen**: API global de eventos y noticias.
- **Query de Consulta**: `Panama AND (logistica OR turismo OR economia OR canal)`.
- **Formato**: Ingesta JSON & CSV.
- **Cobertura Geográfica**: Centroamérica y cuenca del Canal.
- **Licencia**: Dominio público / Uso abierto de investigación académica.

### 2.3. Fuente 3: Banco Mundial Open Data (Indicadores Macroeconómicos)
- **Tipo de Origen**: API REST v2 de indicadores mundiales.
- **Endpoint**: `https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json`
- **Indicadores Clave Extraídos**:
  - `NY.GDP.MKTP.KD.ZG`: Crecimiento del PIB (% anual).
  - `FP.CPI.TOTL.ZG`: Inflación, precios al consumidor (% anual).
  - `SL.UEM.TOTL.ZS`: Desempleo total (% de la fuerza laboral).
  - `BX.KLT.DINV.WD.GD.ZS`: Inversión Extranjera Directa (% del PIB).
  - `GC.DOD.TOTL.GD.ZS`: Deuda pública (% del PIB).
  - `FM.LBL.BMNY.GD.ZS`: Masa monetaria amplia (% del PIB).
- **Países en Catálogo**: Panamá (`PAN`) como foco principal; pares regionales de referencia: Costa Rica (`CRI`), Colombia (`COL`), República Dominicana (`DOM`), México (`MEX`), Guatemala (`GTM`).
- **Formato**: CSV tabular (`indicadores.csv`).
- **Licencia**: Creative Commons Attribution 4.0 International (CC BY 4.0). Requiere cita explícita de fuente y año.

### 2.4. Fuente 4: USGS Earthquake Catalog (Eventos Sísmicos)
- **Tipo de Origen**: GeoJSON API de monitoreo sísmico mundial.
- **Bounding Box Geoespacial**: Latitudes `[5.0, 12.0]`, Longitudes `[-86.0, -76.0]` (zona de convergencia Panamá-Colombia-Costa Rica).
- **Formato**: FeatureCollection GeoJSON estándar (`eventos.geojson`).
- **Propiedades Clave**:
  - `mag`: Magnitud en escala de Richter o momento sísmico.
  - `place`: Descripción geográfica de referencia.
  - `time`: Timestamp Unix en milisegundos.
  - `geometry.coordinates`: `[longitud, latitud, profundidad]`.
- **Licencia**: Dominio público de los Estados Unidos (U.S. Geological Survey).

---

## 3. Políticas de Transformación y Calidad del Dato

1. **Conservación Estricta de Nulos (T01 & T04)**:  
   Cuando un indicador o fecha no está disponible en la fuente de origen, el sistema almacena `None` / `null`. **Queda terminantemente prohibido imputar ceros (`0.0`) a valores faltantes**, para evitar distorsionar el cálculo de variaciones o alertar sobre datos inexistentes.
2. **Tolerancia a Fechas No Parseables**:  
   Si una noticia contiene una cadena de fecha mal formada o un valor no estándar, el loader no arroja una excepción fatal; preserva el valor original en los metadatos y establece el campo estructurado como `None`.
3. **Detección de Recirculación de Noticias Antiguas (T03)**:  
   Si un artículo reporta un evento con fecha de publicación original de años anteriores (e.g. mayo de 2022) que es republicado en 2024, el sistema preserva la marca original y etiqueta la ficha con la advertencia de recirculación para evitar que sea tratada como un suceso de última hora.
4. **Sanitización de Inyecciones de Prompt (T07)**:  
   Todo texto proveniente de fuentes externas se encapsula en contenedores `<source_data>` y se desinfecta de patrones de secuestro de instrucciones antes de ser suministrado a los modelos de lenguaje.

---

## 4. Manifiesto Criptográfico Oficial (`data/manifest.json`)

El archivo `data/manifest.json` constituye la prueba de inmutabilidad del corpus de referencia:

```json
{
  "version": "v1.0",
  "fecha_corte_utc": "2026-10-06T20:00:40.206271+00:00",
  "consultas": [
    "TVN RSS Panama",
    "GDELT DOC 2.0 Panama logistica turismo economia",
    "World Bank Indicators (PAN, CRI, COL, DOM, MEX, GTM)",
    "USGS Earthquake Catalog Box [5,12] [-86,-76]"
  ],
  "cantidad_por_archivo": {
    "noticias.csv": 10,
    "indicadores.csv": 14,
    "eventos.geojson": 3
  },
  "licencia_condiciones": "Ver licencias específicas por archivo en items. Uso exclusivo hackIAthon.",
  "archivos": [
    {
      "archivo": "raw/noticias.csv",
      "cantidad_registros": 10,
      "licencia": "Derechos de autor TVN/GDELT - Uso referencial",
      "sha256": "e74363790a311bc626aca4c0b3252d86a5987f3056f8104062fe193abda8d7e4",
      "transformaciones": "Deduplicación y normalización UTC"
    },
    {
      "archivo": "raw/indicadores.csv",
      "cantidad_registros": 14,
      "licencia": "CC BY 4.0 (Banco Mundial / SBP)",
      "sha256": "0a9776ea862e7bcbcb8482e8933654ab6a855166bcfe4a576eb987e004de3b58",
      "transformaciones": "Conservación de nulos y tipos numéricos"
    },
    {
      "archivo": "raw/eventos.geojson",
      "cantidad_registros": 3,
      "licencia": "Dominio público (USGS)",
      "sha256": "1d0a27d3c56127f3bdcddd5c2315c1aff2442c5e78d342cf9e54d634cb85b6a2",
      "transformaciones": "Filtrado regional lat 5-12, lon -86 a -76"
    }
  ]
}
```

El comando `make manifest` permite verificar y recalcular estos hashes en cualquier momento para certificar la integridad del entorno.
