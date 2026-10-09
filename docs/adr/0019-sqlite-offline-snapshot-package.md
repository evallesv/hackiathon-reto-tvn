# ADR-0019: Paquete de snapshot local y consultable en SQLite

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Contexto**: El reto requiere un paquete de datos congelado, reproducible y disponible durante una demo sin conexión. El proyecto ya tenía CSV/GeoJSON como entrada del corpus y `copilot.db` como almacenamiento mutable para ingesta y revisión. Usar solo la base operativa como snapshot mezclaría evidencia con historial de ejecución y decisiones humanas; depender únicamente de archivos separados tampoco aprovecha SQLite para consultas locales.

## Decisión

Se conserva el paquete raw congelado como procedencia y contrato de intercambio, y se empaqueta su contenido en `data/snapshot/snapshot.sqlite` para consulta local. Al construir el paquete desde una máquina que tenga una base operativa, se incorporan noticias de los últimos 90 días y las series/eventos vivos disponibles, con precedencia por URL, clave de indicador e ID USGS. La extracción lee SQLite en modo de solo lectura y no copia tablas de revisión ni bitácoras de ingesta.

El paquete se publica como directorio atómico con `snapshot_manifest.json`, hash del archivo SQLite, hash del manifiesto raw, corte temporal, conteos y hash del contenido vivo incluido. El adaptador de snapshot abre la base en modo de solo lectura. La aplicación usa el snapshot solo cuando esos hashes y la versión de esquema son válidos; en otro caso usa los archivos raw como respaldo. El entorno de pruebas continúa usando exclusivamente sus fixtures deterministas.

El benchmark y sus etiquetas permanecen fuera de la base de evidencia. La base de snapshot es corpus consultable; no es un conjunto de entrenamiento ni una partición de evaluación.

## Consecuencias

- La demo puede consultar una copia autocontenida de noticias, indicadores y eventos sin red ni un servidor de base de datos.
- Una captura local puede incluir noticias recientes ya ingeridas, aunque la base operativa original se desconecte o cambie después.
- Los datos de revisión humana y las bitácoras operativas no contaminan el corpus congelado.
- Los archivos raw siguen siendo necesarios para procedencia, licencias y reconstrucción; SQLite pasa a ser la representación local de consulta.
- La base no aumenta por sí sola la cobertura del corpus. El manifiesto y la auditoría siguen exponiendo faltantes de volumen o de cuadrícula de indicadores.

## Conformidad con el reto

Implementa el almacenamiento de la arquitectura mínima de la sección 8, mejora la reproducibilidad offline T10 y entrega un artefacto con hash y metadatos como solicita la sección 10. La separación de benchmark preserva la evaluación de desarrollo y evita presentar el snapshot como entrenamiento supervisado.
# Corrección de integridad USGS (2026-10-09)

El contrato actual de eventos exige campos numéricos no nulos. Al empaquetar la base operativa,
un evento incompatible se rechaza con su ID y el motivo antes de publicar el paquete; no se
imputan ceros ni se publica silenciosamente un corpus parcial. Los loaders de consulta excluyen
features inválidas con diagnóstico y continúan con las válidas. El dato operativo nulo se conserva
en su base. Admitir eventos parciales en el modelo requiere ampliar explícitamente el contrato.
