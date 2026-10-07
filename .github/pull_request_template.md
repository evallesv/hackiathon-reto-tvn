## 🎯 Resumen del Cambio
<!-- Breve descripción de qué resuelve este PR, por qué es necesario y qué componentes modifica -->

### Tipo de Cambio
- [ ] `feat`: Nueva funcionalidad o conector
- [ ] `fix`: Corrección de bug o invariante
- [ ] `docs`: Documentación o ADR
- [ ] `refactor`: Refactorización sin cambio funcional
- [ ] `test`: Nuevas pruebas o mejoras de cobertura
- [ ] `chore`: Mantenimiento, dependencias o configuración

## 🔗 Issue Relacionado
<!-- Closes #123 o Relates to #456 (requerido para rastreabilidad) -->

---

## 🌿 Protocolo Git & Desarrollo Multi-Agente
- [ ] **Rama Aislada**: El PR proviene de una rama específica (`feat/...`, `fix/...`, `agent/...`), NUNCA de `main`.
- [ ] **Rebase con `origin/main`**: La rama está sincronizada con `git rebase origin/main` (sin commits de merge espurios ni historial contaminado).
- [ ] **Commits Atómicos y Legibles**: Cada commit sigue la especificación Conventional Commits (`tipo(alcance): descripción`) y describe una unidad lógica de cambio.
- [ ] **Protección de Producción (Fly.io)**: Se verificó que este cambio no tumbe la máquina de producción al mergear (puerto `0.0.0.0:8080`, dependencias congeladas en `uv.lock`, compatibilidad con SQLite `/data/copilot.db`).

---

## 📋 Checklist de Calidad en AI Engineering
- [ ] **Verificación Local Completa (`make check`)**:
  - `uv run ruff check .` (0 errores)
  - `uv run ruff format --check .` (0 observaciones)
  - `uv run mypy src/` (Success: no issues found)
  - `uv run pytest` (60/60 tests aprobados, T01–T10 intactos)
- [ ] **100% Citas Verificables**: Ninguna afirmación factual generada carece de cita vinculada a `id_fuente`.
- [ ] **Escudo Anti-Inyección**: Toda entrada externa se aísla en etiquetas `<source_data>` y se desinfecta como dato no confiable.
- [ ] **Independencia de Evidencia**: El estado de evidencia no se confunde con el puntaje de atención; `INSUFICIENTE` bloquea publicación.
- [ ] **Corpus Congelado Intacto**: No se modificaron `data/raw/` ni `data/manifest.json` (a menos que sea una regeneración explícita autorizada con `make manifest`).
- [ ] **Cero Secretos**: No se incluyeron tokens, credenciales, claves de API ni cambios al archivo `.env`.
- [ ] **Decisión Arquitectónica (ADR)**: Si el cambio introduce un nuevo patrón, proveedor o flujo estructural, se registró o actualizó un ADR en `docs/adr/`.
