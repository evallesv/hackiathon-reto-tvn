# ADR-0013: Unificación de Ruteo de Modelos System One y System Two mediante OpenCode API

* **Estado**: Aceptado
* **Fecha**: 2026-10-07
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

Previamente, la arquitectura requería múltiples proveedores y claves API independientes para ejecutar el pipeline editorial:
1. **System One (Decisión)**: Cloudflare Workers AI (`CLOUDFLARE_API_TOKEN`) o TypeSafe AI (`TYPESAFE_API_KEY`).
2. **System Two (LLM Generativo)**: OpenCode API (`OPENCODE_API_KEY`) o Gemini (`GEMINI_API_KEY`).

Esta fragmentación aumentaba la complejidad de configuración del entorno de desarrollo y despliegue, incrementaba la superficie de error en credenciales y dispersaba el esfuerzo del equipo.

Dado que la plataforma **OpenCode** ofrece acceso unificado tanto al modelo generativo **Muse Spark** (`muse-spark-1.3-contributor`) a través de OpenCode Go (`https://opencode.ai/zen/go/v1`) como a los modelos de decisión System One de TypeSafe **Jev** (`jev-1.13-free`) a través del gateway OpenCode Zen (`https://opencode.ai/zen/v1/systemone`), se decidió unificar el ruteo de ambos sistemas bajo una única variable de entorno: `OPENCODE_API_KEY`.

## Decisión

1. **Unificación de Credenciales bajo `OPENCODE_API_KEY`**:
   - `JevAdapter` (System One) y `OpenCodeAdapter` (System Two) reutilizan transparentemente `OPENCODE_API_KEY`.
   - Si `TYPESAFE_API_KEY` no se define, el factory `get_decision_client` utiliza automáticamente `OPENCODE_API_KEY`.

2. **Ruteo de System One (Jev en OpenCode Zen)**:
   - Endpoint por defecto: `https://opencode.ai/zen/v1/systemone`.
   - Modelo por defecto: `jev-1.13-free`.
   - Serialización de preguntas adaptada a la especificación de Jev:
     - `ScoreQuestion`: Se serializa con rúbrica ordenada de niveles (`criteria`) para retornar distribuciones continuas calibradas normalizadas a `[0.0, 1.0]`.
     - `ChoiceQuestion`: Mapeo de opciones a criterios para selección categórica y detección de hecho vs. declaración.
     - `NoulQuestion`: Respuestas probabilísticas binarias para detección de contradicciones (**T05**).

3. **Ruteo de System Two (Muse Spark en OpenCode Go)**:
   - Endpoint por defecto: `https://opencode.ai/zen/go/v1`.
   - Modelo por defecto: `muse-spark-1.3-contributor`.
   - Soporte para protocolo OpenAI Responses (`/responses`) y Chat Completions (`/chat/completions`).
   - Encabezado oficial requerido por OpenCode Go: `x-opencode-session: <uuid>` inyectado automáticamente por petición para garantizar afinidad de enrutamiento y caché sin estado residual.

4. **Resiliencia Offline y Compatibilidad Retroactiva**:
   - Si no se proporcionan credenciales, el sistema mantiene fallback transparente a los adaptadores `MockDecisionAdapter` y `MockLLMAdapter` para garantizar reproducibilidad sin red (**T10**).
   - Se mantiene la compatibilidad opcional con Cloudflare Clef y Google Gemini si el usuario decide activarlos explícitamente vía configuración.

## Consecuencias

### Positivas
- **Configuración Simple (Zero Friction)**: Una única clave (`OPENCODE_API_KEY`) habilita todo el pipeline de producción (decisión, rúbrica, clasificación y redacción editorial).
- **Cero Fragmentación**: Se evita depender de múltiples cuentas y tokens externos en desarrollo y despliegue.
- **Conformidad con Políticas**: Uso legítimo y documentado de OpenCode Go y OpenCode Zen con encabezado de sesión de acuerdo con las especificaciones de la plataforma.

### Compromisos
- En OpenCode Go, modelos que entrenan con datos de peticiones requieren habilitar el permiso de privacidad en la cuenta del usuario si se configuran modelos específicos.
