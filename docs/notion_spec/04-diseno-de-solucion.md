# 04 — Diseño de la Solución y Arquitectura Técnica

> **Espacio Oficial de Presentación en Notion Business**  
> **Arquitectura Hexagonal, Modelo de Datos, Fórmula Explicable de Scoring y Prompts Seguros**

---

## 1. Diagrama de Arquitectura Hexagonal (Ports & Adapters)

El diseño desacopla rigurosamente las reglas del dominio periodístico de cualquier biblioteca de infraestructura, base de datos o proveedor de LLM:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CAPA WEB & UI                                        │
│  FastAPI Endpoints (/api/v1/copilot/*)  │  Dashboard HTML5/CSS/JS (Dark Glassmorphism)  │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CAPA DE SERVICIOS & CASOS DE USO                          │
│        CopilotService (Orquestador Editorial)  │  BaselineEvaluator (Benchmark)        │
└──────────────────┬─────────────────────────────────────────────────┬───────────────────┘
                   ▼                                                 ▼
┌─────────────────────────────────────┐           ┌──────────────────────────────────────┐
│       PUERTOS DE ENTRADA / SALIDA   │           │           NÚCLEO DE DOMINIO          │
│ - BaseDecisionClient (System One)   │           │ - models.py (Pydantic Inmutables)    │
│ - BaseLLMClient (System Two)        │           │ - scoring.py (Fórmula P y Desempate) │
│ - BaseStorageRepository (Datos)     │           │ - safety.py (Anti-Inyección y Citas) │
└──────────────────┬──────────────────┘           └──────────────────────────────────────┘
                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CAPA DE ADAPTADORES                                  │
│  Decision: CloudflareClef │ Jev │ Mock  │  LLM: OpenCode Muse-Spark │ Gemini │ Mock    │
│  Data: CsvLoader │ GeoJsonLoader │ SQLiteStorage (WAL) │ LiveFetchers (RSS/WB/USGS)    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Modelo de Contratos de Datos (Pydantic v2)

Todos los contratos residen en `domain/models.py` y se rigen por la regla estricta de nombres en `snake_case` minúsculas:

- **`Noticia`**: Representa el cable o artículo extraído con fecha UTC, medio emisor, alcance de texto (`titular_metadatos` o `cuerpo_completo`) y metadatos.
- **`Indicador`**: Serie temporal económica con `pais_iso3`, `indicador_id`, `anio`, `valor` (`float | None`), `unidad` y fuente oficial.
- **`EventoGeoJSON`**: Suceso sísmico o geográfico con magnitud, latitud, longitud, profundidad y marca temporal.
- **`FichaCaso`**: Objeto central de inteligencia informativa con:
  - `id_caso` (`str`): Identificador único (e.g. `CASO-001`).
  - `modalidad` (`Modalidad`): `tvn_editorial` o `banca`.
  - `ids_fuente` (`list[str]`): Lista de fuentes vinculadas.
  - `afirmaciones` (`list[Afirmacion]`): Declaraciones individuales clasificadas por tipo (`hecho`, `declaracion`, `inferencia`) con citas vinculadas.
  - `citas` (`list[CitaEvidencia]`): Citas que sustentan el caso.
  - `puntaje` (`float`): Puntuación $P \in [0.0, 100.0]$.
  - `componentes` (`ComponentesPuntaje`): Desglose de $R, I, U, N, E \in [0.0, 1.0]$.
  - `estado_evidencia` (`EstadoEvidencia`): `insuficiente`, `parcial`, `suficiente_para_borrador`.
  - `borrador` (`dict`): Paquete editorial TVN o boletín bancario.
  - `estado_revision` (`EstadoRevision`): `nuevo`, `en_revision`, `aprobado_como_borrador`, `descartado`, `requiere_evidencia`.
  - `persona_revisora` (`str | None`): Editor humano responsable.

---

## 3. Fórmula Matemática Explicable de Atención Editorial

La prioridad de cada evento informativo se calcula mediante la fórmula lineal canónica:

$$P = 30R + 25I + 20U + 15N + 10E$$

Donde cada componente está normalizado en el intervalo $[0.0, 1.0]$:
- **$R$ (Relevancia Editorial, 30%)**: Alineación con la agenda país y líneas temáticas clave de TVN (institucionalidad, servicios públicos, canal, economía).
- **$I$ (Impacto Potencial, 25%)**: Amplitud de la población afectada y repercusión socioeconómica.
- **$U$ (Urgencia de Cobertura, 20%)**: Proximidad temporal del suceso y exigencia de emisión inmediata.
- **$N$ (Novedad Informativa, 15%)**: Elementos no reportados previamente frente a historias en desarrollo o recirculadas.
- **$E$ (Evidencia Disponible, 10%)**: Robustez, pluralidad y verificación de los datos de soporte.

### 3.1. Bandas de Prioridad No Solapadas
- **Banda Alto**: $P \in [70.0, 100.0]$ &rarr; Tratamiento prioritario en portada y apertura de noticiero.
- **Banda Medio**: $P \in [40.0, 70.0)$ &rarr; Cobertura en bloques secundarios o seguimiento digital.
- **Banda Bajo**: $P \in [0.0, 40.0)$ &rarr; Monitoreo de fondo sin asignación de recursos inmediatos.

### 3.2. Reglas de Desempate Determinista
Si dos casos obtienen exactamente el mismo puntaje $P$:
1. **Primer criterio de desempate**: Mayor valor en Urgencia ($U$).
2. **Segundo criterio de desempate**: Orden alfanumérico lexicográfico creciente del `id_caso`.

### 3.3. Invariante Guardrail T08 (Independencia de Evidencia)
El puntaje de atención $P$ es independiente del estado de evidencia. Un caso puede tener $P = 83.8$ (Banda Alto), pero si su `estado_evidencia == INSUFICIENTE`, **el sistema bloquea automáticamente la generación y publicación del borrador (`can_publish_draft() == False`)** y emite una alerta para investigación periodística humana.

---

## 4. Segregación System One (Decisión) vs. System Two (Generación)

| Dimensión | System One (Decisión & Clasificación) | System Two (Generación Explicativa) |
| :--- | :--- | :--- |
| **Rol** | Evaluar $R, I, U, N, E$ y detectar contradicciones factuales (T05). | Redactar borradores editoriales, guiones de TV y justificaciones analíticas. |
| **Adaptadores** | `CloudflareClefAdapter` (`@cf/cloudflare/clef`), `JevAdapter`, `MockDecisionAdapter`. | `OpenCodeAdapter` (`muse-spark-1.3`), `GeminiAdapter` (`gemini-2.5-flash`), `MockLLMAdapter`. |
| **Naturaleza** | Estructurada, determinista, baja latencia (< 50 ms), salida numérica o booleana. | Generación de lenguaje natural con citas embebidas y cumplimiento de longitudes. |
| **Resiliencia** | Fallback automático a heurísticas locales si el token no está configurado. | Fallback automático a `MockLLMAdapter` para operación 100% offline (T10). |

---

## 5. Diseño de Prompts y Mitigación de Inyecciones (T07)

Los textos de noticias externas, cables de agencias y feeds RSS se consideran **datos no confiables por definición**. Para neutralizar intentos de manipulación o secuestro de instrucciones (prompt injection), se implementan dos barreras en `domain/safety.py`:

1. **Aislamiento en Bloques de Datos**: Los textos externos se encierran estrictamente en bloques delimitados:
   ```xml
   <source_data>
   Título: MOP anuncia plan de obras en la capital
   Contenido: Se iniciarán desvíos a partir del lunes...
   </source_data>
   ```
2. **Sanitización de Patrones de Inyección**: Se neutralizan secuencias como:
   - `Ignore previous instructions / Ignora todas las instrucciones`
   - `Reveal system prompt / Muestra las claves del sistema`
   - Escapes de etiquetas XML (`</source_data>`, `-->`, etc.).

---

## 6. Supuestos y Límites del Sistema

1. **Límites de Longitud Editorial**:
   - TVN Brief: Máximo 250 palabras.
   - Copy Digital: Máximo 80 palabras.
   - Guion Televisivo: Cadencia de 45 a 60 segundos (aproximadamente 110-150 palabras habladas).
2. **Atribución ante Metadatos Únicos**:
   - Si una noticia sólo contiene titular o metadatos sin cuerpo desarrollado, el borrador incluye explícitamente la cláusula: `"basado únicamente en titular/metadatos"`.
3. **Reserva Humana Absoluta**:
   - La IA nunca decide de forma autónoma la veracidad de una información ni aprueba borradores para emisión directa.
