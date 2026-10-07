# 05 — Casos de Estudio y Fichas de Evidencia

> **Espacio Oficial de Presentación en Notion Business**  
> **Catálogo de 5 Fichas Canónicas Trazables, Borradores Editoriales y Demostración de Guardrails**

---

## 1. Tabla Resumen de los 5 Casos Canónicos

| ID Caso | Modalidad | Título Resumido | Score $P$ | Banda | Estado Evidencia | Guardrail Destacado | Estado Revisión |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`CASO-001`** | TVN Editorial | MOP inicia rehabilitación de vías en Ciudad de Panamá | **80.0** | Alto | Suficiente para borrador | Cobertura de citas 100% (T09) | Aprobado como borrador |
| **`CASO-002`** | TVN Editorial | ACP eleva calado operacional a 45 pies por mejora en embalses | **84.25** | Alto | Suficiente para borrador | Deduplicación de múltiples fuentes (T02) | En revisión |
| **`CASO-003`** | TVN Editorial | Reporte de colapso de puente vial en el interior | **47.5** | Medio | Parcial | Detección de noticia recirculada de 2022 (T03) | Requiere evidencia |
| **`CASO-004`** | Banca (CU-05) | PIB crece 7.3% e inflación moderada en 1.5% en 2023 | **73.75** | Alto | Suficiente para borrador | Preservación exacta indicadores Banco Mundial (T04) | Aprobado como borrador |
| **`CASO-005`** | TVN Editorial | Rumor no corroborado en redes sobre corte de servicios | **83.75** | Alto | **Insuficiente** | **ALERTA T08: Publicación bloqueada por falta de pruebas** | Requiere evidencia |

---

## 2. Detalle Exhaustivo de las Fichas de Caso

### Caso 1: `CASO-001` — Rehabilitación de Vías en la Capital (MOP)
- **Modalidad**: TVN Editorial.
- **Fuentes Vinculadas**: `NOT-001`, `NOT-007` (Comunicado oficial MOP y despacho informativo).
- **Puntaje de Atención**: $P = 80.0$ ($R=0.85, I=0.80, U=0.75, N=0.70, E=0.90$).
- **Estado de Evidencia**: `suficiente_para_borrador`.
- **Afirmaciones y Citas de Respaldo**:
  - `AF-001-1` [HECHO]: *"MOP anuncia plan de rehabilitación de vías en la Ciudad de Panamá."*  
    *Cita*: `NOT-001` (campo: `titulo`) &rarr; [https://www.tvn-2.com/nacionales/mop-rehabilitacion-vias-panama_1.html](https://www.tvn-2.com/nacionales/mop-rehabilitacion-vias-panama_1.html).
- **Borrador Editorial TVN**:
  - **Titular Propuesto**: *"Obras Viales en la Capital: MOP Inicia Plan de Mantenimiento Integral"*.
  - **Brief Editorial (67 palabras, límite 250)**: *"El Ministerio de Obras Públicas confirmó la puesta en marcha de un programa de rehabilitación vial en puntos neurálgicos de la Ciudad de Panamá. El plan responde a demandas de transportistas y residentes de zonas metropolitanas de alto tráfico. Toda la información procede de los comunicados de prensa y despachos de agencias cotejados por el equipo editorial."*
  - **Guion Televisivo (45-60s)**: Lectura estimada de 52 segundos sobre cronogramas y desvíos vehiculares.
  - **Copy Digital (25 palabras, límite 80)**: *"Mantenimiento vial en marcha: MOP anuncia intervención en vías principales de la capital. Conoce los tramos y lo que demandan los conductores. #TVNNoticias #Panama"*.
  - **Preguntas de Investigación**:
    1. ¿Cuál es el cronograma detallado de cierres parciales por corregimiento?
    2. ¿Qué empresas contratistas asumirán las garantías por vicios ocultos de las obras?
    3. ¿Cuál es el presupuesto fiscal comprometido por el ministerio para esta fase?
- **Revisión Humana**: Aprobado por María González (Editora Jefa).

---

### Caso 2: `CASO-002` — Aumento de Calado en el Canal de Panamá (ACP)
- **Modalidad**: TVN Editorial.
- **Fuentes Vinculadas**: `NOT-002`, `NOT-003`, `NOT-102`, `NOT-103` (4 artículos sobre el mismo suceso unificados en una sola procedencia, cumpliendo el test **T02**).
- **Puntaje de Atención**: $P = 84.25$ ($R=0.95, I=0.90, U=0.70, N=0.65, E=0.95$).
- **Estado de Evidencia**: `suficiente_para_borrador`.
- **Afirmaciones y Citas de Respaldo**:
  - `AF-002-1` [HECHO]: *"ACP reporta aumento de calado operacional a 45 pies ante mejora en embalses."*  
    *Cita*: `NOT-003` (campo: `titulo`) &rarr; [https://www.panamaamerica.com.pa/economia/calado-canal-45-pies_3.html](https://www.panamaamerica.com.pa/economia/calado-canal-45-pies_3.html).
- **Enfoque de Interés Público**: Aumento en capacidad de tránsito para portacontenedores e ingresos para el Tesoro Nacional.
- **Revisión Humana**: `EN_REVISION` por Roberto Quintero (Productor Digital).

---

### Caso 3: `CASO-003` — Detección de Noticia Recirculada (Puente en el Interior)
- **Modalidad**: TVN Editorial.
- **Fuente Vinculada**: `NOT-009`.
- **Puntaje de Atención**: $P = 47.5$ (Banda Medio). Urgencia $U=0.20$ debido a la antigüedad del hecho.
- **Invariante Verificado (T03)**: El artículo reporta una noticia fechada originalmente el **10 de mayo de 2022**. Aunque fue republicada en redes en 2024, el sistema detecta la recirculación, preserva la fecha original y bloquea el borrador como noticia de última hora.
- **Estado de Evidencia**: `parcial`.
- **Revisión Humana**: `REQUIERE_EVIDENCIA` por Carlos Bethancourt (Verificador). Nota: *"NOTICIA RECIRCULADA (T03): Corresponde a mayo de 2022. No emitir como primicia"*.

---

### Caso 4: `CASO-004` — Extensión de Banca: Entorno Macroeconómico (CU-05)
- **Modalidad**: Banca (Boletín de Entorno Macroeconómico y Logístico).
- **Fuentes Vinculadas**: `PAN-NY.GDP.MKTP.KD.ZG-2023`, `PAN-FP.CPI.TOTL.ZG-2023`, `NOT-004`.
- **Puntaje de Atención**: $P = 73.75$ (Banda Alto).
- **Invariante Verificado (T04)**: Mantiene los valores exactos oficiales del Banco Mundial para Panamá en 2023 (PIB: 7.3%, Inflación: 1.5%) sin imputar ceros ni alterar unidades.
- **Afirmaciones y Citas**:
  - `AF-004-1` [HECHO]: *"Panamá registró un crecimiento del PIB de 7.3% y una inflación de 1.5% en 2023."*  
    *Cita*: `PAN-NY.GDP.MKTP.KD.ZG-2023` &rarr; API Banco Mundial.
- **Boletín Bancario Generado**:
  - **Sectores Relacionados**: Logística portuaria, comercio minorista, construcción, banca comercial.
  - **Horizonte Temporal**: 2024Q1 - 2024Q4.
  - **Hipótesis de Impacto**: *"La combinación de crecimiento económico e inflación baja favorece la estabilidad en la calidad crediticia agregada del sistema financiero"*.
  - **Preguntas para el Analista de Riesgo**:
    1. ¿Cuál es la correlación histórica entre el PIB de 7.3% y la morosidad de la cartera corporativa?
    2. ¿Qué resiliencia presentan los operadores logísticos ante fluctuaciones en tasas internacionales?
- **Revisión Humana**: Aprobado por Elena Torres (Analista Senior de Riesgo).

---

### Caso 5: `CASO-005` — Demostración Explícita del Guardrail T08 (Rumor en Redes)
- **Modalidad**: TVN Editorial.
- **Fuente**: `NOT-010` (Fuente no institucional / rumor viral).
- **Puntaje de Atención**: **$P = 83.75$ (Banda Alto)** debido a su alta relevancia percibida ($R=0.90$), enorme impacto potencial ($I=0.95$) y urgencia extrema ($U=0.90$).
- **Estado de Evidencia**: **`INSUFICIENTE` ($E=0.15$)**.
- **Comportamiento del Guardrail T08**:
  - A pesar de que el puntaje de atención colocaría esta noticia en el primer puesto de la agenda, **el método `can_publish_draft()` evalúa `False`**.
  - El sistema **prohíbe estrictamente la generación del borrador publicable**, borra el borrador automático y activa una alerta en rojo en el dashboard:  
    `"ALERTA T08: Puntaje de atención alto (83.8) con evidencia insuficiente exige investigación periodística independiente; NUNCA habilita publicación ni generación de borrador."`
- **Revisión Humana**: `REQUIERE_EVIDENCIA` por Carlos Bethancourt (Verificador).
