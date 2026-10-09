# ADR-0015: Dashboard Web Interactivo Embebido (Dark Glassmorphism)

* **Estado**: Aceptado
* **Fecha**: 2026-10-07
* **Área**: Frontend, Experiencia de Usuario (UX) y Demostración al Jurado

---

## 1. Contexto y Planteamiento del Problema

La evaluación en vivo ante el jurado del HackIAthon (Sección 5 y 10 de las bases) requiere una superficie interactiva en tiempo real para:
1. Inspeccionar el ranking dinámico de la agenda y la descomposición visual de la fórmula $P = 30R + 25I + 20U + 15N + 10E$.
2. Auditar las fichas de caso, la clasificación de afirmaciones (`hecho`, `declaracion`, `inferencia`) y sus citas directas (**T09**).
3. Demostrar el flujo editorial de supervisión humana (*Human-in-the-Loop*), permitiendo aprobar, requerir evidencia o rechazar borradores con persistencia en SQLite.
4. Someter el sistema a pruebas inmediatas de los criterios mandatorios (**T04**, **T05**, **T06**, **T07**) mediante una consola de evaluación.
5. Visualizar las métricas del benchmark y la integridad criptográfica SHA-256 del manifiesto.

### Restricciones Técnicas
* **Cero Dependencias Pesadas de Node.js / NPM**: La imagen de contenedor de producción en Fly.io y el entorno offline de contingencia (**T10**) no deben depender de herramientas externas de compilación frontend (como Vite, Webpack o Next.js) que puedan fallar por conectividad o incrementar el tamaño de la imagen Docker.
* **Estética Profesional de Primera Clase**: Interfaz moderna, tipo centro de inteligencia de medios (Dark Glassmorphism, paleta TVN Media con acentos cian, rojo y esmeralda).

---

## 2. Alternativas Evaluadas

1. **SPA Externa en React / Next.js**:
   - *Descarte*: Requiere entorno Node.js separado, pipeline de build adicional en CI/CD y riesgo de fallos en despliegues offline de Fly.io.
2. **Streamlit / Gradio**:
   - *Descarte*: Interfaces rígidas, alta latencia en re-renderizados, difícil personalización estética y dependencias pesadas no estándar para salas de redacción.
3. **Frontend Nativo Embebido en FastAPI con Vanilla HTML5/CSS/JS (Elegida)**:
   - Archivos estáticos servidos directamente por FastAPI (`ui/index.html`, `ui/styles.css`, `ui/app.js`) sin empaquetadores ni dependencias npm.

---

## 3. Decisión Adoptada

1. **Estructura Embebida en `src/hackiathon_reto_tvn/ui/`**:
   - `index.html`: Estructura semántica con 4 vistas tabuladas, identificadores únicos para automatización y modal de revisión humana.
   - `styles.css`: Sistema de diseño Dark Glassmorphism (`backdrop-filter: blur(16px)`), variables CSS, animaciones suaves y soporte responsivo.
   - `app.js`: Lógica cliente reactiva modular sin librerías externas que consume directamente la API REST del copiloto.
2. **Montaje en FastAPI (`main.py`)**:
   - `app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")`
   - Rutas raíz `GET /` y `GET /dashboard` sirviendo `index.html` mediante `FileResponse`.
3. **4 Vistas Funcionales**:
   - **Vista 1 (Agenda Priorizada)**: Tarjetas explicables, barras de componentes y banner activo de Guardrail **T08**.
   - **Vista 2 (Fichas & Borradores)**: Selector de casos, inspector de citas y afirmaciones, paquetes multiformato (Brief 250 palabras, Guion 45-60s, Copy 80 palabras, Extensión Banca) y modal de revisión.
   - **Vista 3 (Consola del Jurado)**: Botones de prueba instantánea (T04, T05, T06, T07, USGS) y consola de consulta libre.
   - **Vista 4 (Métricas & Benchmark)**: KPIs dinámicos, tabla comparativa de baselines y verificador de hashes SHA-256.

---

## 4. Consecuencias y Beneficios

* **Autonomía Total y Velocidad**: Cero segundos de tiempo de compilación frontend; despliegue instantáneo con `uv run hackiathon-server`.
* **Cumplimiento Estricto de T10**: Funciona al 100% de forma local y offline sin requerir acceso a internet.
* **Demostración de Alto Impacto**: Permite al jurado validar la solución de forma visual e intuitiva durante el pitch de 10 minutos.
