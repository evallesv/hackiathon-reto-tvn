## 🎯 Resumen del Cambio
<!-- Breve descripción de qué resuelve este PR y qué componentes modifica -->

## 🔗 Issue Relacionado
<!-- Closes #123 o Relates to #456 -->

## 📋 Checklist de Calidad en AI Engineering
- [ ] **100% Citas Verificables**: Ninguna afirmación factual generada carece de cita (`id_fuente`).
- [ ] **Escudo Anti-Inyección**: La entrada externa es tratada estrictamente como dato, no instrucción.
- [ ] **Independencia de Evidencia**: El estado de evidencia no se confunde con el puntaje de atención.
- [ ] **Pruebas y Tipado**:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run mypy src/`
  - `uv run pytest`
- [ ] **Cero Secretos**: No se incluyeron tokens, claves de API ni contraseñas en el código ni en los commits.
- [ ] **ADR Actualizado**: Si aplica, se registró la decisión arquitectónica en `docs/adr/`.
