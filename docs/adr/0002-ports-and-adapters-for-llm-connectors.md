# ADR-0002: Arquitectura Hexagonal para Conectores LLM Intercambiables (OpenCode y Gemini)

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El reto exige la capacidad de intercambiar modelos de lenguaje sin alterar la lógica de negocio ni los flujos de extracción de evidencias.
Específicamente:
* El proveedor **por defecto** es **OpenCode** utilizando el modelo `muse-spark-1.3-contributor-free`.
* El proveedor alternativo es **Google Gemini** (ej. `gemini-2.5-flash`).
* Adicionalmente, el caso de prueba **T10** exige que el prototipo pueda ejecutarse de forma demostrable y determinista **sin acceso a internet** (fallback offline).

## Decisión

Implementar el patrón de **Arquitectura Hexagonal (Ports & Adapters)**:
1. **Puerto (`src/hackiathon_reto_tvn/ports/llm_port.py`)**: Interfaz abstracta `BaseLLMClient` con métodos `generate_text(...)` y `generate_structured(...)`.
2. **Adaptador OpenCode (`OpenCodeAdapter`)**: Implementación sobre la interfaz OpenAI-compatible que apunta a `OPENCODE_BASE_URL` (por defecto `https://api.opencode.ai/v1`) y utiliza el modelo `muse-spark-1.3-contributor-free`.
3. **Adaptador Gemini (`GeminiAdapter`)**: Implementación nativa usando el SDK oficial `google-genai` con soporte de esquemas estructurados Pydantic.
4. **Adaptador Mock (`MockLLMAdapter`)**: Proveedor determinista sin I/O de red, fundamental para pruebas unitarias en CI y para cumplir la prueba de contingencia T10 sin conexión a internet.
5. **Fábrica (`get_llm_client`)**: Inyección de dependencias basada en la variable de entorno `LLM_PROVIDER` (`opencode` \| `gemini` \| `mock`).

## Consecuencias

### Positivas
* Independencia absoluta de la capa de dominio frente a cambios de API o cuotas de terceros.
* Conmutación instantánea cambiando una variable de entorno (`LLM_PROVIDER=gemini` o `LLM_PROVIDER=opencode`).
* Pruebas unitarias ultrarrápidas, repetibles y con costo cero ($0.00) vía `MockLLMAdapter`.

### Negativas / Compromisos
* Cada nuevo proveedor debe implementar tanto la generación de texto libre como la validación de esquemas JSON estructurados.
