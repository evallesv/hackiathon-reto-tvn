# ADR-0020: Validación de límites editoriales antes de guardar borradores

- **Estado**: Aceptado
- **Fecha**: 2026-10-09
- **Área**: Dominio / Entregables editoriales

## Contexto

El reto establece límites de extensión para los entregables de TVN: brief de hasta 250 palabras, copy digital de hasta 80 palabras y guion de 45 a 60 segundos. La configuración ya declaraba esos valores, pero el servicio persistía y devolvía cualquier salida del proveedor, incluso si excedía esos límites. El boletín bancario también exige un resumen de hasta 250 palabras.

## Decisión

Validar de forma determinista los borradores después de generarlos y antes de calcular su cobertura de citas o guardarlos en la ficha. El conteo usa una función pura del dominio. Para el guion se configura un ritmo de 150 palabras por minuto: los 45–60 segundos corresponden a 113–150 palabras. Si un entregable viola un límite, el servicio lo rechaza y no cambia el estado de revisión ni persiste el borrador.

## Consecuencias

- Las reglas funcionan igual con proveedores reales y mock, y no dependen del framework HTTP.
- Las pruebas demuestran rechazo de brief y copy demasiado largos, guion demasiado corto y ausencia de persistencia ante rechazo.
- El ritmo de lectura es una estimación operativa configurable; la revisión editorial humana sigue siendo necesaria para duración real, claridad, contenido y sustento semántico.

## Conformidad con el reto

Hace cumplir de manera verificable los límites del paquete editorial y del resumen bancario. No sustituye la aprobación humana ni afirma que el conteo léxico valide relevancia o calidad periodística.
