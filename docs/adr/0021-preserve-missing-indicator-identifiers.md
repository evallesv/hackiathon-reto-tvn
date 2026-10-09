# ADR-0021: Preservar identificadores faltantes en indicadores

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Área**: Datos / Contratos World Bank

## Contexto

El loader convertía columnas ausentes de país y año a `PAN` y `2024`. Esa imputación cambia el significado del registro y puede atribuir una cifra a un país o periodo que la fuente no indicó. El contrato de datos exige conservar nulos y tipos nativos.

## Decisión

Los identificadores `pais_iso3`, `indicador_id` y `anio` del modelo `Indicador` admiten `None`. El loader convierte valores ausentes o malformados a nulo, sin asignar país o periodo por defecto. El paquete SQLite permite almacenarlos. La auditoría de la cuadrícula requerida sigue exigiendo claves completas y contabiliza esos registros como inválidos; preservarlos no implica considerarlos evidencia válida para una serie.

## Consecuencias

- Los datos faltantes no se transforman en hechos ficticios y sobreviven la carga y el snapshot.
- Las consultas por país, indicador y año no seleccionan filas sin esas claves.
- La auditoría puede diferenciar entre conservar el registro y cumplir la cobertura del conjunto evaluable.

## Conformidad con el reto

Refuerza T01/T04 y la reproducibilidad del snapshot sin convertir nulos en ceros, Panamá o 2024.
