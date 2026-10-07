# 01 — Inicio del Reto: Copiloto de Inteligencia Informativa con IA

> **Espacio Oficial de Presentación en Notion Business**  
> **HackIAthon 4ta Edición**: *De la señal a la decisión: Copiloto de inteligencia informativa y análisis de entorno con IA*  
> **Entidad Desafiante**: TVN Media (con extensión modular para sector Banca)  
> **Equipo**: Sentria AI Core Engineers

---

## 1. Identificación del Equipo y Roles

| Rol | Responsable | Funciones Clave |
| :--- | :--- | :--- |
| **Lead AI Architect & Domain Engineering** | Sentria Team | Arquitectura Hexagonal, Invariantes de Dominio, Scoring $P$, Guardrails T01-T10 |
| **Data & Reliability Engineer** | Sentria Team | Ingesta SQLite WAL, Criptografía SHA-256, World Bank & USGS Fetchers |
| **Fullstack & Newsroom UX Engineer** | Sentria Team | FastAPI Backend, Dark Glassmorphism Dashboard, Flujos Human-in-the-loop |
| **Ethics, Safety & Evaluation Lead** | Sentria Team | Anti-Injection Shield, Benchmark 60 Consultas, 100% Citation Coverage |

---

## 2. Definición del Problema

### El Dolor en la Sala de Redacción de TVN Media
1. **Sobrecarga de Señales (Infoxicación)**: Los redactores reciben miles de despachos diarios (cables, comunicados ministeriales, alertas en redes sociales y teletipos). Separar la señal relevante del ruido requiere horas de tamizaje manual.
2. **Conflicto Celeridad vs. Verificación**: La presión por la primicia mediática induce errores graves: publicar noticias recirculadas de años anteriores (T03), citar cifras sin trazabilidad (T01) o dar crédito a versiones contradictorias sin verificación (T05).
3. **Riesgo Crítico de Alucinación de la IA Generativa**: Los modelos comerciales responden con aplomo inventando fuentes, fechas o indicadores económicos inexistentes, lo que destruiría la credibilidad editorial de TVN.
4. **Falta de Adaptación Modular**: La información macroeconómica y logística de Panamá raramente se traduce en insumos de valor para analistas sectoriales de riesgo bancario (CU-05).

---

## 3. Usuario Objetivo y Casos de Uso

### 3.1. Usuarios Primarios (TVN Media)
- **Editores de Mesa Central / Jefatura de Emisión**: Requieren un ranking explicable de la agenda del día para asignar reporteros y ordenar el noticiero vespertino.
- **Periodistas y Redactores Digitales**: Requieren paquetes iniciales trazables (Brief < 250 palabras, Copy Digital < 80 palabras, Guion TV 45-60s) con el 100% de los hechos respaldados por citas verificables.
- **Fact-Checkers y Verificadores**: Requieren alertas inmediatas si una noticia de alto impacto carece de sustento suficiente (T08) o contradice versiones oficiales (T05).

### 3.2. Usuario Secundario (Analista de Banca y Finanzas)
- **Analista de Riesgo Sectorial y Entorno Macroeconómico**: Requiere boletines sintéticos sobre PIB, inflación y eventos logísticos (Canal de Panamá) sin inferencias no fundamentadas ni decisiones automatizadas de crédito individual.

---

## 4. Alcance de la Solución

| En Alcance (In Scope) | Fuera de Alcance (Out of Scope) |
| :--- | :--- |
| **Priorización Explicable de Agenda**: Fórmula $P = 30R + 25I + 20U + 15N + 10E$ con desempate determinista. | Calificación categórica binaria automatizada de "Verdadero o Falso" (reserva humana obligatoria). |
| **Fichas de Evidencia Trazables**: Extracción de hechos, declaraciones e inferencias con cita obligatoria a `id_fuente`. | Publicación directa o automática sin revisión humana explícita (`EN_REVISION` &rarr; `APROBADO`). |
| **Borradores Multi-Formato TVN**: Generación de brief, guion televisivo y copy digital ajustados a restricciones editoriales. | Modificación o sobreescritura de los datasets congelados del reto (`data/raw/`). |
| **Extensión Modular de Banca (CU-05)**: Boletín sectorial agregado con indicadores del Banco Mundial. | Evaluación de riesgo crediticio individual o perfilamiento de clientes bancarios. |
| **Consola Interactiva del Jurado**: Ejecución en vivo de consultas libres y los 10 criterios de aceptación (T01-T10). | Modelos generativos sin conexión a fuentes o con tolerancia a la alucinación. |

---

## 5. Criterios de Éxito del Proyecto (KPIs Oficiales)

1. **100% de Cobertura de Citas (T09)**: Toda afirmación fáctica generada en un borrador está vinculada a un ID de fuente verificado.
2. **100% de Tasa de Abstención Explícita (T06)**: Si el corpus no contiene evidencia, el sistema responde `[ABSTENCIÓN EXPLÍCITA]` sin inventar.
3. **100% de Neutralización de Inyecciones de Prompt (T07)**: Los textos de fuentes externas se tratan como datos no confiables dentro de bloques `<source_data>`.
4. **Mejora Significativa sobre Baselines**:
   - Priorización: Mejora de al menos +50% en Precision@5 frente a la recencia temporal ingenua (logrado: **+100.0%**).
   - Clasificación: Macro-F1 de System One superior a heurísticas de expresiones regulares (logrado: **0.941 vs 0.647, +45.4%**).
5. **Operabilidad 100% Offline y Determinista (T10)**: Demostración y suite de pruebas ejecutables sin internet ni tokens de pago.
6. **Despliegue Productivo Continuo**: Despliegue en la nube mediante Fly.io con persistencia SQLite WAL y binding en `0.0.0.0:8080`.

---

## 6. Accesos Rápidos al Ecosistema

- **Dashboard Interactivo en Vivo**: `http://localhost:8080/` o `https://tvn-copilot.fly.dev/`
- **Documentación Interactiva OpenAPI / Swagger**: `http://localhost:8080/docs`
- **Repositorio GitHub**: `https://github.com/evallesv/hackiathon-reto-tvn`
- **Rama de Solución Completa**: `feat/copilot-e2e-solution`
- **Suite de Verificación**: `make check` (Ruff, Mypy, Pytest 80/80 green)
