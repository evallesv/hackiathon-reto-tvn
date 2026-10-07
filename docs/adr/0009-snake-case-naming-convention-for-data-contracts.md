# ADR-0009: Convención de Nombres `snake_case` para Contratos de Datos y API

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA
* **Relacionado con**: [ADR-0008](0008-data-contract-reproducibility-and-manifest.md) (contrato del manifiesto)

## Contexto

Los modelos de `src/hackiathon_reto_tvn/domain/models.py` son simultáneamente el contrato de dominio, el esquema JSON de `data/manifest.json` y el esquema de respuesta/solicitud de la API (FastAPI serializa los campos de Pydantic tal cual). Cualquier nombre inconsistente se filtra por lo tanto a los consumidores externos (jurado, Notion, clientes HTTP).

Una revisión encontró una inconsistencia en el contrato `Manifest`: el campo `fecha_corte_UTC` mezclaba `snake_case` con un sufijo en mayúsculas, mientras que el resto de los campos (`fecha_publicacion`, `fecha_extraccion`, `cantidad_por_archivo`, ...) son `snake_case` en minúsculas. La regla de lint `N815` (mixedCase) está desactivada en `pyproject.toml` y, de todos modos, no detecta el patrón `snake_case_MAYÚSCULAS`, por lo que ninguna herramienta lo señaló.

## Decisión

1. **Convención**: toda propiedad de un contrato de datos (modelos de `domain/models.py`, claves de `manifest.json`, `fichas.jsonl`, cuerpos y respuestas de la API) usa `snake_case` en **minúsculas** (`^[a-z][a-z0-9]*(_[a-z0-9]+)*$`). Las siglas y unidades se escriben en minúsculas: `fecha_corte_utc`, `pais_iso3`, `sha256`. Los nombres de clase siguen `PascalCase`; el vocabulario de dominio sigue en español (ver `AGENTS.md`).
2. **Renombrado**: `Manifest.fecha_corte_UTC` → `Manifest.fecha_corte_utc`, aplicado en:
   * el modelo `Manifest` y `LocalStorageRepository.generate_manifest`;
   * la respuesta de `GET /api/v1/copilot/manifest`;
   * `data/manifest.json` (solo se renombra la clave; el valor del timestamp y todos los hashes SHA-256 permanecen intactos, por lo que la integridad del snapshot congelado no cambia).
3. **Sin alias heredado**: no se mantiene `fecha_corte_UTC` como alias de lectura ni de serialización. Es un cambio incompatible en la API; se prefiere un contrato único y sin ambigüedad.
4. **Aplicación automática**: `tests/test_domain_invariants.py` valida por reflexión que *todos* los campos de *todos* los modelos de dominio, y todas las claves de `data/manifest.json`, cumplan la expresión regular anterior. `tests/test_api.py` y `tests/test_data_loaders.py` verifican que la clave heredada ya no aparece.
5. **Excepción documentada**: `EventoGeoJSON` conserva nombres en inglés (`magnitude`, `time`, `place`, ...) porque refleja el esquema externo del catálogo USGS. Cumple el patrón `snake_case` pero no el idioma; se registra en la sección de brechas de `AGENTS.md`.

## Alternativas consideradas

* **Mantener el nombre y documentarlo**: rechazada; perpetúa la inconsistencia en un contrato público.
* **Alias de Pydantic (`validation_alias`/`serialization_alias`) para aceptar ambos nombres**: rechazada; añade dos nombres para el mismo dato y retrasa indefinidamente la migración. Puede reconsiderarse si se descubre un consumidor externo del nombre anterior.
* **Solo activar `N815` en ruff**: insuficiente; no detecta `snake_case_MAYÚSCULAS`.

## Consecuencias

### Positivas
* Contrato único y predecible en código, JSON y API.
* Una regresión de nombres falla en CI (pruebas) en lugar de depender de la revisión manual.

### Compromisos
* **Cambio incompatible** para cualquier cliente que lea `fecha_corte_UTC` de `/api/v1/copilot/manifest` o de un `manifest.json` antiguo: `Manifest.model_validate` rechazará manifiestos con la clave anterior. Un manifiesto antiguo debe regenerarse (`make manifest`) o migrarse renombrando la clave.
* Si el reglamento del reto exige literalmente `fecha_corte_UTC` en `manifest.json`, esta decisión debe revisarse antes de la entrega (ver Conformidad).

## Conformidad con el Reto

Las pruebas T01–T10 no dependen del nombre de este campo. El requisito de la sección 6/7 del reto es que el manifiesto contenga la *fecha de corte UTC*; el nombre exacto de la clave debe confirmarse contra las bases oficiales.
