# ADR-0022: Agrupamiento determinista de noticias por similitud léxica

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Área**: Datos / Agrupamiento de eventos

## Contexto

Agrupar por los primeros tres tokens del titular puede separar titulares parafraseados y combinar historias distintas que comienzan con frases genéricas. La agrupación debe evitar inflar la corroboración al reunir cobertura sindicada del mismo evento.

## Decisión

Normalizar acentos y puntuación, excluir palabras funcionales y aperturas genéricas frecuentes, y conectar pares de titulares cuando comparten al menos dos términos y esos términos cubren al menos el 60% del titular más corto. Si ambas fechas de publicación están disponibles, se exige una diferencia de hasta 14 días. Se forman grupos por componentes conexos y se mantiene el orden original de los artículos.

## Consecuencias

- Los titulares con entidades o términos de evento compartidos se agrupan aunque cambie el orden de las palabras.
- Las aperturas genéricas como «Gobierno anuncia plan» dejan de dominar la agrupación.
- La regla es reproducible y no necesita red ni dependencias adicionales.
- Sigue siendo una heurística léxica: no detecta equivalencias completas sin vocabulario común y requiere evaluación etiquetada antes de reportar precisión o recall.

## Conformidad con el reto

Reduce duplicados y corroboración inflada para T02, con casos de paráfrasis y titulares distintos bajo una apertura genérica.
