# ADR-0026: Preparación de adjudicación humana y atribución del proveedor efectivo

**Estado:** Aceptado  
**Fecha:** 2026-10-09

## Contexto

La sección 9.1 exige numeradores, denominadores, fallos, falsas abstenciones y revisión humana del sustento
de al menos treinta afirmaciones si se producen tantas. El benchmark previo medía IDs y valores literales;
podía atribuir resultados del fallback mock al nombre del adaptador remoto configurado.

## Decisión

- Guardar respuestas/citas de desarrollo y listas de fallos por ID. Contar abstenciones incorrectas sobre
  todas las consultas etiquetadas como respondibles, manteniéndolas en el denominador de exactitud.
- Propagar proveedor/modelo del `DecisionResult` y contar ejecuciones por proveedor efectivo, separadas
  del adaptador configurado. Una ejecución con fallback no acredita desempeño del modelo remoto.
- Preparar una planilla local con respuestas y registros originales del corpus. Las afirmaciones,
  veredictos, responsables y fechas permanecen vacíos hasta la revisión humana. Una respuesta puede
  contener varias afirmaciones y no se usa como sustituto automático del tamaño de muestra exigido.
- Admitir solo reportes de desarrollo en el exportador local; las consultas reservadas y sus reportes
  permanecen fuera del proyecto. Estar fuera del repositorio no prueba independencia ni custodia.
- Representar tokens/costo no instrumentados con `null`; no inventar mediciones ni deducir costo cero
  a partir del fallback. La revisión semántica permanece pendiente hasta contar con veredictos humanos.

## Consecuencias

El editor dispone de material concreto para identificar y juzgar cada afirmación, incluyendo detalles
factuales de respuestas y borradores completos. Los resultados automáticos siguen siendo exploratorios.
La planilla preparada no acredita la meta de sustento ≥90%, evaluación ciega, ahorro operativo ni ejecución
de una capacidad NLP/ML sustantiva. Estas evidencias requieren personas y ejecuciones identificadas.

## Verificación

Regresiones offline simulan una falsa abstención y un adaptador remoto que devuelve `DecisionResult` mock.
El reporte cuenta el fallo y atribuye las diez decisiones al proveedor real. El exportador preserva
registros originales y no crea veredictos; rechaza un reporte reservado. `make check` pasó con 197 pruebas
en la integración de estos cambios.
