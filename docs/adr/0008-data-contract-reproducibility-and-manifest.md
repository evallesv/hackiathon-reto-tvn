# ADR-0008: Contrato de Datos, Ingesta No Bloqueante y Manifiesto Criptográfico SHA-256

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

La sección 6 y 7 del reto definen el paquete de datos públicos congelados:
* `noticias.csv`: 200 registros meta (mínimo 100, al menos 20 de TVN).
* `indicadores.csv`: 6 países (PAN, CRI, COL, DOM, MEX, GTM), 2010–2024, 6 indicadores del Banco Mundial.
* `eventos.geojson`: Catálogo sísmico del USGS 2024 para la caja regional latitud 5–12, longitud −86 a −76; magnitud mínima 3.
* `fichas.jsonl`: Formato serializado de casos procesados.
* `manifest.json`: Versión, fecha de corte UTC, consultas, cantidad por archivo, licencia, SHA-256 y transformaciones.

Reglas de integridad esenciales:
1. Usar UTF-8, IDs estables y fechas ISO 8601 en UTC.
2. Conservar nulos y unidades originales; no rellenar ausencia de datos con cero (Prueba T01 y T04).
3. Cada afirmación debe referenciar el ID de evidencia y el campo/pasaje correspondiente.

## Decisión

1. Definir los modelos de datos tipados en `src/hackiathon_reto_tvn/domain/models.py` (`Noticia`, `Indicador`, `EventoGeoJSON`, `Manifest`).
2. Implementar ingesta no bloqueante en `LocalStorageRepository.load_noticias`: errores en filas aisladas no detienen la carga del resto del archivo (Prueba T01).
3. Generador automatizado de manifiesto criptográfico (`generate_manifest`) que calcula el checksum SHA-256 de cada archivo en `data/raw/` y genera `data/manifest.json`.
4. Suite de pruebas específicas `test_data_loaders.py` y `test_acceptance_t01_t10.py` que validan el contrato de datos.

## Consecuencias

### Positivas
* 100% de reproducibilidad para el jurado.
* Protección contra corrupción de datos o desalineación de esquemas en tiempo de ejecución.

## Addendum (2026-10-06): nombre del campo de fecha de corte

El campo del manifiesto que contiene la fecha de corte UTC se llama `fecha_corte_utc` (antes `fecha_corte_UTC`), según la convención `snake_case` en minúsculas definida en [ADR-0009](0009-snake-case-naming-convention-for-data-contracts.md). El cambio afecta al modelo `Manifest`, a `generate_manifest`, a `data/manifest.json` y a la respuesta de `GET /api/v1/copilot/manifest`. Los hashes SHA-256 de `data/raw/` no cambian.

## Addendum (2026-10-09): GDELT `seendate`

GDELT `seendate` es el momento en que el servicio detectó el artículo, no la fecha original de publicación. El adaptador lo conserva en `fecha_deteccion` y deja `fecha_publicacion` vacía si no puede verificarla por separado.
