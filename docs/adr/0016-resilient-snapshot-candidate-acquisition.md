# ADR-0016: Reintentos y publicación atómica de snapshots candidatos

* **Estado**: Aceptado
* **Fecha**: 2026-10-08
* **Área**: Ingesta, reproducibilidad y cumplimiento de datos

## Contexto

La preparación del dataset del reto consulta TVN RSS, GDELT, World Bank y USGS. Los proveedores pueden limitar solicitudes, devolver errores transitorios o responder con datos truncados. Un CSV rellenado artificialmente con nulos o un directorio escrito a medias puede parecer completo aunque la extracción haya fallado.

## Decisión

1. Reintentar respuestas HTTP 429 y errores 5xx, además de fallos de red y timeout, hasta cuatro intentos. Respetar `Retry-After` y usar espera exponencial con jitter cuando el servidor no indique una espera.
2. Limitar solicitudes concurrentes al Banco Mundial a tres. Restringir GDELT a su máximo documentado de 250 resultados y subdividir secuencialmente las ventanas saturadas; restringir USGS a 20 000 resultados y rechazar respuestas que alcancen ese límite.
3. En modo estricto, una solicitud fallida del Banco Mundial invalida la extracción. No sintetizar filas de combinaciones que la API no devolvió; conservar nulos solo cuando el Banco Mundial devolvió explícitamente esa combinación.
4. Construir en un directorio temporal vecino y publicar mediante renombrado atómico solo si pasan todos los criterios de auditoría. Si falla cualquier fuente o mínimo, borrar el staging y conservar un informe lateral `<destino>.audit-report.json`; nunca crear el directorio final como snapshot incompleto.
5. No sobrescribir destinos existentes. Las extracciones fallidas se vuelven a ejecutar en una ruta nueva para conservar evidencia previa.

## Consecuencias

* Una limitación temporal del proveedor puede alargar la ejecución, pero el número de intentos es finito y el servidor controla la espera mediante `Retry-After`.
* Un snapshot incompleto deja un informe diagnóstico con cobertura y errores de fuente, pero no se confunde con un dataset listo.
* La publicación final es atómica: los consumidores ven el snapshot completo o no ven la ruta final.
