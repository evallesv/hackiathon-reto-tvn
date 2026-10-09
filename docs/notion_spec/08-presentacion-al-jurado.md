# 08 — Guión de Presentación Oficial al Jurado (Pitch de 10 Minutos)

> **Espacio Oficial de Presentación en Notion Business**  
> **Estructura Cronometrada, Guión Verbal, Demostración en Vivo y Respuestas Clave ante el Jurado**

---

## 1. Estructura y Cronograma del Pitch (10 Minutos)

| Bloque Temporal | Sección | Objetivo Principal | Pantalla / Recurso a Proyectar |
| :---: | :--- | :--- | :--- |
| **0:00 – 1:30** (1.5 min) | **1. El Dolor en TVN Media** | Plantear el conflicto entre velocidad de primicia y rigor editorial; el peligro de las alucinaciones de la IA. | Diapositiva 1 / Dashboard Header |
| **1:30 – 3:00** (1.5 min) | **2. Arquitectura de Decisión** | Explicar la Arquitectura Hexagonal y la segregación System One (Decisión rápida) vs System Two (LLM explicativo). | Diagrama C4 / Fórmula de Atención $P$ |
| **3:00 – 6:30** (3.5 min) | **3. Demostración en Vivo** | Recorrido interactivo por las 4 vistas del dashboard: Agenda, Ficha, Consola del Jurado y Métricas. | **Dashboard Web en Vivo (`http://localhost:8080`)** |
| **6:30 – 8:00** (1.5 min) | **4. Benchmark y Baselines** | Mostrar resultado exploratorio, baseline, tamaño de muestra y limitaciones; presentar resultados de IA solo si se verifican antes del pitch. | Vista 4 / Gráficos de Evaluación |
| **8:00 – 9:00** (1.0 min) | **5. Ética y Guardrails** | Destacar el guardrail T08, anti-inyección T07 y supervisión humana obligatoria. | Guardrail Alert T08 / Modal de Revisión |
| **9:00 – 10:00** (1.0 min) | **6. Impacto y Cierre** | Retorno de inversión para TVN Media, extensión bancaria y despliegue productivo. | Conclusión / Preguntas y Respuestas |

---

## 2. Guión Verbal Paso a Paso para los Expositores

### Minuto 0:00 – 1:30: El Problema en la Redacción
> *"Muy buenos días, señores miembros del jurado. En la era digital, las salas de redacción como la de TVN Media no sufren por falta de información, sino por infoxicación. Cada día llegan miles de cables, alertas en redes y comunicados oficiales.  
> La presión por ganar la primicia induce dos grandes riesgos: difundir noticias falsas o recirculadas de años anteriores, y peor aún, si intentamos usar IA generativa comercial sin control, los modelos alucinan cifras y fuentes inventadas.  
> Por eso hoy presentamos el **Copiloto de Inteligencia Informativa de TVN Media**: un sistema diseñado para transformar la señal cruda en decisiones editoriales seguras, trazables y auditables."*

---

### Minuto 1:30 – 3:00: La Solución Arquitectónica
> *"Nuestra solución se apoya en dos pilares arquitectónicos:  
> Primero: **Arquitectura Hexagonal Pura**, donde las reglas de negocio no dependen de proveedores comerciales ni requieren conexión a internet para operar de forma 100% determinista.  
> Segundo: **Segregación de Sistemas cognitivos**:  
> Usamos un **System One** (modelos de decisión de ultrabaja latencia como Cloudflare Clef o Jev) para clasificar señales y priorizar la agenda en menos de un milisegundo mediante una fórmula matemática explicable:  
> $$P = 30\% \text{ Relevancia} + 25\% \text{ Impacto} + 20\% \text{ Urgencia} + 15\% \text{ Novedad} + 10\% \text{ Evidencia}$$  
> Y reservamos el **System Two** (modelos generativos como OpenCode Muse-Spark o Gemini) exclusivamente para redactar borradores finales cuando —y sólo cuando— la evidencia está plenamente verificada."*

---

### Minuto 3:00 – 6:30: Demostración en Vivo en el Dashboard

*(El expositor proyecta el Dashboard en `http://localhost:8080/`)*

#### Paso 1: Vista 1 — Agenda Priorizada & Guardrail T08
> *"Veamos el sistema en acción. Aquí en la **Vista 1: Agenda Priorizada**, observamos el ranking en tiempo real. Fíjense en la tarjeta de la Autoridad del Canal de Panamá (`CASO-002`), que encabeza la agenda con un puntaje de **84.2**. Aquí el sistema unificó cuatro despachos distintos sobre el mismo suceso en una sola procedencia (cumpliendo el test **T02**).  
> Pero miren esta alerta roja en la parte superior: el caso `CASO-005` es un rumor viral con alto impacto y urgencia que acumula un puntaje de 83.8; sin embargo, su evidencia es insuficiente. Aquí opera nuestro **Guardrail T08**: la IA bloquea automáticamente la generación del borrador y le dice al periodista: 'Investigue primero, prohibido publicar'."*

#### Paso 2: Vista 2 — Fichas de Caso, Citas 100% y Control Humano
*(Hacer clic en la tarjeta de `CASO-001` - Obras Viales del MOP)*
> *"Al ingresar a la **Ficha de Caso**, vemos que cada afirmación está etiquetada como hecho, declaración o inferencia (test **T09**). Pero lo más importante: **el 100% de los hechos cuenta con una cita textual verificada hacia la fuente original**.  
> El copiloto genera automáticamente el **Brief Editorial de menos de 250 palabras**, el **Guion de televisión de 45 a 60 segundos**, el **Copy para redes de 80 palabras** y 3 preguntas clave de investigación ciudadana.  
> Y respetamos el principio de **Human-in-the-Loop**: el borrador está en estado 'En Revisión'. Ninguna noticia sale al aire sin que un editor humano haga clic en 'Aprobar Borrador' registrando su nombre y notas."*

#### Paso 3: Vista 3 — Consola Interactiva del Jurado
*(Hacer clic en la pestaña 'Consola del Jurado')*
> *"Invitamos al jurado a someter a prueba el sistema. Tenemos botones de prueba inmediata:  
> - Si presionamos **[T04]**, el sistema consulta el PIB y la inflación de Panamá 2023: extrae de inmediato el 7.3% y 1.5% del Banco Mundial con cita al indicador oficial.  
> - Si presionamos **[T06]**, preguntando por ingresos turísticos de 2029 que no están en el corpus, el sistema **no alucina ni inventa cifras**: emite inmediatamente una **Abstención Explícita**.  
> - Si presionamos **[T07]**, con un ataque de inyección de prompt que ordena ignorar instrucciones y revelar contraseñas, el sistema lo neutraliza, lo aísla como texto plano y mantiene íntegro el sistema.  
> - Y con el **Detector de Contradicciones (T05)**, comparamos dos versiones sobre el calado del Canal y el modelo System One detecta la inconsistencia side-by-side en milisegundos."*

---

### Minuto 6:30 – 8:00: Validación Científica y Resultados del Benchmark
*(Hacer clic en la pestaña 'Métricas & Benchmark')*
> *"Tenemos 40 consultas de desarrollo ejecutables. Las 20 etiquetas reservadas quedaron dentro del repositorio y no son ciegas, así que el runner las excluye y necesitamos custodia independiente para evaluar al jurado. En el snapshot SQLite local, P@5 fue 0 de 5 por recencia y 2 de 5 con la fórmula; son etiquetas por palabras clave, no una selección editorial independiente. En diez pares sintéticos, Macro-F1 fue 0.792 para regex y 0.524 para el adaptador mock. Las tasas estructurales de citas no verifican por sí solas el sustento semántico de cada oración."*

---

### Minuto 8:00 – 9:00: Ética, Gobernanza y Extensión Banca (CU-05)
> *"En materia ética, el sistema está blindado: respeta los derechos de autor de TVN y las licencias CC BY 4.0 del Banco Mundial. Nunca imputa ceros a datos faltantes (T01) y nunca toma decisiones autónomas de calificación.  
> Además, demostramos la modularidad de nuestra arquitectura en el caso `CASO-004`, donde el mismo motor genera un **Boletín Macroeconómico y Logístico para analistas de riesgo bancario**, conectando el PIB y los embalses del Canal con el entorno sectorial."*

---

### Minuto 9:00 – 10:00: Conclusión e Impacto de Negocio
> *"En resumen: hemos construido una solución productiva, desplegada en Fly.io con persistencia en SQLite WAL, con 80 pruebas automatizadas pasando al 100%, y una interfaz pensada para el ritmo frenético de una sala de redacción.  
> El Copiloto de TVN Media permite a los periodistas llegar primero, pero sobre todo, **llegar con la verdad verificada**.  
> Muchas gracias. Quedamos a su disposición para las preguntas del jurado."*

---

## 3. Guía de Respuestas a Posibles Preguntas del Jurado

1. **¿Qué ocurre si se cae el servicio de internet o la API de OpenCode durante la emisión en vivo?**  
   *Respuesta*: *"El sistema cuenta con el adaptador `MockLLMAdapter` y `MockDecisionAdapter` como fallback automático y transparente. El sistema sigue priorizando la agenda, validando citas y generando paquetes editoriales con datos locales sin detener la redacción (cumplimiento del criterio T10)."*
2. **¿Por qué la IA no dice directamente si una noticia es Verdadera o Falsa?**  
   *Respuesta*: *"Porque etiquetar de forma binaria 'Verdadero/Falso' introduce falsos positivos peligrosos y delega la responsabilidad editorial en un algoritmo. Nuestro copiloto proporciona la evidencia, las discrepancias entre fuentes y las preguntas pendientes, dejando el dictamen ético en manos del periodista humano."*
3. **¿Cómo garantizan que la fórmula de atención $P$ no tenga sesgos?**  
   *Respuesta*: *"A diferencia de un modelo de caja negra, cada componente ($R, I, U, N, E$) es visible de forma transparente en el dashboard con sus ponderaciones auditadas y desempate determinista por urgencia."*
