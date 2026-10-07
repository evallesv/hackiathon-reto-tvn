# ADR-0012: Flujo Git para Desarrollo Multi-Agente, Estandarización en AGENTS.md y Protección de Main

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El proyecto integra capacidades de ingeniería de IA operadas concurrentemente por desarrolladores humanos y múltiples agentes de codificación autónomos (Antigravity, Cursor, Copilot, Cline, Claude Code, OpenCode). Durante el ciclo de desarrollo acelerado del reto, surgen tres riesgos operativos críticos:

1. **Riesgo de Caída en Producción**: La rama `main` está enlazada al pipeline de despliegue continuo automático a Fly.io Machines (`.github/workflows/fly-deploy.yml`). Cualquier commit o push directo a `main` sin validación previa puede tumbar el servicio activo en producción.
2. **Colisiones y Deuda en Historial Git**: Múltiples agentes o desarrolladores trabajando en paralelo sobre `main` generan conflictos de fusión frecuentes, "merge bubbles" (commits de fusión desordenados tipo `Merge branch 'main' of ...`) y commits heterogéneos difíciles de auditar o revertir.
3. **Dispersión de Instrucciones de Agente**: Existían archivos duplicados o de redirección como `CLAUDE.md`, cuando los principales frameworks y asistentes de código de la industria (incluyendo Claude Code, Antigravity, Cursor y Cline) han adoptado el estándar unificado `AGENTS.md`.

## Decisión

1. **Estandarización Exclusiva en `AGENTS.md`**:
   - Se elimina de forma permanente `CLAUDE.md`.
   - `AGENTS.md` se establece como la única fuente canónica e inmutable de directrices de desarrollo, arquitectura y protocolo de ejecución para todos los agentes de IA.

2. **Protección Inviolable de la Rama `main`**:
   - **Cero Commits Directos**: Queda terminantemente prohibido realizar commits directos o push a `main`.
   - **Puerta de Entrada Exclusiva mediante Pull Requests (PR)**: Cualquier modificación debe gestionarse en una rama aislada y solicitar integración vía PR.
   - **Pre-Push Hook Local (`.githooks/pre-push`)**: Se implementa un hook de Git que intercepta cualquier comando `git push` dirigido a `refs/heads/main` y bloquea la operación con una advertencia explicativa.
   - Se habilita la configuración de hooks mediante `make setup-hooks` y se integra de forma transparente en `make install`.

3. **Flujo de Trabajo Git Lineal para Múltiples Usuarios y Agentes**:
   - **Nomenclatura de Ramas**: Ramas cortas y tipadas vinculadas a tareas o issues:
     - `feat/<id>-<slug>`: Nuevas funcionalidades o endpoints.
     - `fix/<id>-<slug>`: Corrección de bugs o invariantes.
     - `docs/<id>-<slug>`: Documentación, diagramas o ADRs.
     - `chore/<id>-<slug>`: Mantenimiento, dependencias o tooling.
     - `agent/<nombre>-<id>-<slug>`: Trabajo específico asignado a un agente autónomo.
   - **Sincronización por Rebase**: Para mantener un historial limpio y legible, se exige actualizar las ramas de trabajo utilizando `git fetch origin && git rebase origin/main` en lugar de crear commits de fusión intermedios (`git merge main`).
   - **Conventional Commits**: Todos los mensajes de commit deben respetar el estándar `tipo(alcance): descripción imperativa en minúsculas` (ej. `feat(scoring): add tie-breaking logic`, `fix(loaders): preserve null dates in csv`).
   - **Commits Atómicos**: Cada commit debe representar un cambio lógico cohesivo, excluyendo archivos temporales, claves `.env`, bases de datos SQLite locales o mutaciones involuntarias en `data/raw/`.

4. **Gate de Validación (`make check`) y Plantilla de PR**:
   - Todo PR debe verificar satisfactoriamente el gate de calidad local `make check` (Ruff linter, Ruff format check, Mypy typecheck y Pytest con 60/60 pruebas y los 10 casos T01–T10) antes de ser propuesto.
   - Se actualiza `.github/pull_request_template.md` con casillas de verificación obligatorias para rebase limpio, ausencia de secretos, invariantes de dominio y seguridad de producción.
   - Estrategia de integración recomendada en GitHub: **Squash and Merge** o **Rebase and Merge** para garantizar un historial lineal en `main`.

## Consecuencias

### Positivas
* **Producción Blindada**: Es imposible tumbar las máquinas en Fly.io por commits inadvertidos o código no probado en `main`.
* **Historial Limpio y Biseccionable**: El árbol de Git permanece 100% lineal, facilitando el uso de `git bisect` y auditorías forenses ante cualquier eventualidad.
* **Coexistencia Multi-Agente Armoniosa**: Múltiples agentes pueden bifurcar ramas a partir de `main`, desarrollar con contratos desacoplados (Hexagonal) y sincronizarse limpiamente sin sobreescribir el trabajo ajeno.
* **Unificación Normativa**: Todos los asistentes y agentes leen exactamente las mismas instrucciones en `AGENTS.md`.
