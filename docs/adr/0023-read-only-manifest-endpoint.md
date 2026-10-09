# ADR-0023: Endpoint de manifiesto estrictamente de solo lectura

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Área**: API / Reproducibilidad

## Contexto

El endpoint HTTP de manifiesto leía archivos directamente desde la capa de rutas y, si faltaba `manifest.json`, invocaba la generación del manifiesto sobre el directorio activo. Una consulta GET no debe regenerar ni cambiar el conjunto congelado.

## Decisión

La ruta delega la operación a `CopilotService.get_reproducibility_manifest()`. El servicio solo lee y valida el manifiesto existente. Si no está presente, la API devuelve 404 y no intenta crearlo.

## Consecuencias

- La capa HTTP solo traduce la solicitud y los errores del caso de uso.
- Consultar integridad no puede modificar los archivos evaluados.
- La generación sigue siendo una operación explícita de tooling (`make manifest`) y no una consecuencia de una lectura.

## Conformidad con el reto

Protege la inmutabilidad del snapshot y mantiene las fronteras hexagonales descritas para la API.
