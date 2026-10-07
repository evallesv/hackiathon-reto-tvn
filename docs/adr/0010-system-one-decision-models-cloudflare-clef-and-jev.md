# ADR-0010: Modelos de Decisión System One (Cloudflare Clef y TypeSafe Jev) para Clasificación y Scoring

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El copiloto de TVN Media requiere realizar tareas críticas de toma de decisiones antes de generar cualquier contenido:
1. Ponderación de componentes de atención ($R, I, U, N, E$) según relevancia nacional, impacto, urgencia y novedad.
2. Clasificación categórica de afirmaciones (`hecho` vs `declaración` vs `inferencia`).
3. Detección de contradicciones o discrepancias entre fuentes (Requisito de Aceptación **T05**).
4. Evaluación del estado de suficiencia de la evidencia para prevenir alucinaciones (Requisito **T08**).

Anteriormente, los componentes $R, I, U, N$ se estimaban mediante heurísticas estáticas de palabras clave en el servicio (`copilot_service.py`), identificada como una limitación en la Sección 9 de `AGENTS.md`.

Utilizar un LLM generativo tradicional (System Two) para estas tareas introduce:
- Latencia innecesaria (generación autorregresiva de texto token por token).
- Costos computacionales elevados.
- Mayor variabilidad en el parsing y riesgo de alucinaciones.

En contraste, los **modelos de decisión System One** (popularizados por TypeSafe AI con **Jev** en septiembre de 2026 y estandarizados en código abierto por Cloudflare con **Clef** `@cf/cloudflare/clef` en octubre de 2026) son modelos no generativos optimizados para evaluar un `state` contra un esquema de preguntas tipadas (`noul`, `choice`, `score`), retornando directamente distribuciones de probabilidad y decisiones estructuradas en milisegundos.

## Decisión

1. **Separación de Responsabilidades**:
   - **System One (Modelo de Decisión)**: Encargado exclusivo de clasificación, puntuación de rúbrica, categorización de afirmaciones y detección de discrepancias. Proveedor por defecto: **Cloudflare Clef** (`@cf/cloudflare/clef`), con compatibilidad completa para **TypeSafe Jev** (`jev-latest`) y un adaptador **Mock** determinista offline.
   - **System Two (LLM Generativo)**: Encargado de la redacción, síntesis y estructuración del paquete editorial (`BorradorEditorial`) a través del puerto `BaseLLMClient` existente (`OpenCode`, `Gemini`, `Mock`).

2. **Puerto de Decisión Hexagonal (`src/hackiathon_reto_tvn/ports/decision_port.py`)**:
   - Interfaz abstracta `BaseDecisionClient` con método asíncrono `decide(state, questions) -> DecisionResult`.
   - Contratos para preguntas tipadas: `NoulQuestion` (booleano/probabilidad), `ChoiceQuestion` (clasificación múltiple con opciones y criterios) y `ScoreQuestion` (escala continua / rúbrica).

3. **Adaptadores Desacoplados (`src/hackiathon_reto_tvn/adapters/decision/`)**:
   - `CloudflareClefAdapter`: Conector REST para Workers AI (`https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/clef`).
   - `JevAdapter`: Conector para la API comercial de TypeSafe AI (`https://api.typesafe.ai/v1/systemone`).
   - `MockDecisionAdapter`: Conector offline determinista para pruebas automáticas, CI y contingencia sin internet (**T10**).
   - `factory.py`: Fábrica `get_decision_client` con **fallback transparente a Mock** si las credenciales de Cloudflare o Jev no están presentes en el entorno local.

4. **Concurrencia Configurable**:
   - Evaluación asíncrona de casos en `prioritize_agenda_async` regulada por un semáforo configurable (`DECISION_CONCURRENCY_LIMIT`, por defecto 5 peticiones concurrentes).
   - Wrapper sincrónico `prioritize_agenda` para máxima compatibilidad con llamadas existentes en CLI y suite de pruebas.

## Consecuencias

### Positivas
- **Cero Heurísticas Frágiles**: Los factores de scoring $R, I, U, N$ se alimentan de decisiones probabilísticas calibradas por el modelo de 27B Clef.
- **Detección Formal de Contradicciones (T05)**: Implementación real de detección de discrepancias entre versiones mediante preguntas `noul` evaluadas por Clef/Jev.
- **Rendimiento Óptimo**: Decisiones en <200ms sin incurrir en generación de tokens largos.
- **Offline & CI Resiliente**: Fallback transparente al adaptador Mock cuando no hay credenciales o se ejecutan pruebas unitarias en modo hermético (T10).

### Negativas / Compromisos
- Requiere configurar credenciales de Cloudflare Workers AI (`CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN`) para modo en vivo en producción.
