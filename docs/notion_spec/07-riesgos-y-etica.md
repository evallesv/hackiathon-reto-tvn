# 07 — Riesgos, Ética y Gobernanza del Sistema

> **Espacio Oficial de Presentación en Notion Business**  
> **Gobernanza Editorial, Privacidad, Derechos de Autor, Mitigación de Sesgos y Supervisión Humana**

---

## 1. Principios Éticos y Filosofía Editorial

El Copiloto de Inteligencia Informativa para TVN Media se rige por el principio fundamental de **la IA como amplificador de capacidades humanas, nunca como árbitro autónomo de la verdad informativa**. 

En concordancia con los estándares periodísticos de TVN Media y los principios rectores de la 4ta edición del HackIAthon:
1. **La IA nunca califica noticias como "verdaderas" o "falsas"**: El sistema identifica señales objetivas, contradicciones textuales y fuentes pendientes de verificación. El juicio de credibilidad final es competencia indelegable del equipo periodístico.
2. **Ningún borrador se publica sin aprobación humana expresa**: Todo contenido generado entra en estado `EN_REVISION`; sólo una acción voluntaria de un editor con nombre y cargo transiciona el caso a `APROBADO_COMO_BORRADOR`.
3. **Trazabilidad Absoluta**: Si una afirmación no puede vincularse a una fuente comprobada en el corpus, se descarta o se emite abstención explícita.

---

## 2. Matriz de Riesgos y Medidas de Mitigación

| Riesgo Identificado | Severidad | Probabilidad | Medida de Mitigación Implementada | Verificación Técnica |
| :--- | :---: | :---: | :--- | :--- |
| **Alucinación de Cifras Económicas o Citas** | **Crítica** | Media | Abstención canónica y control conservador de IDs, fragmentos y términos citados. No demuestra implicación semántica ni cubre automáticamente cada oración libre; revisión humana obligatoria. | T06 y control léxico parcial en T09; validación semántica y extracción completa pendientes. |
| **Manipulación por Prompt Injection** | **Alta** | Media | Todo texto externo se trata como dato no confiable en bloques aislados `<source_data>` y se sanitizan instrucciones de escape. | Test de Aceptación **T07** (100% neutralización). |
| **Difusión de Noticias Recirculadas Antiguas** | **Alta** | Alta | Conservación de marcas de tiempo de publicación original y detección de brecha temporal superior a 30 días. | Test de Aceptación **T03** (Puente 2022). |
| **Publicación Precipitada de Primicias sin Evidencia** | **Crítica** | Alta | Guardrail **T08**: si `estado_evidencia == INSUFICIENTE`, la generación y publicación quedan bloqueadas. | Test de Aceptación **T08** (Bloqueo de `CASO-005`). |
| **Infracción de Propiedad Intelectual** | **Media** | Baja | Respeto a términos de licencia por fuente: TVN (uso interno/referencial), Banco Mundial (CC BY 4.0), USGS (dominio público). Cita explícita de autoría. | Catálogo de datos en `data/manifest.json`. |
| **Sesgo Algorítmico en Priorización de Agenda** | **Media** | Media | Fórmula lineal auditada $P = 30R + 25I + 20U + 15N + 10E$ con desglose visual de cada componente en el dashboard. | Test unitario de scoring y rangos no solapados. |
| **Distorsión Estadística por Imputación Errónea** | **Media** | Media | Prohibición absoluta de imputar `0.0` a datos faltantes; conservación estricta de `None` / `null`. | Tests de Aceptación **T01** y **T04**. |

---

## 3. Derechos de Autor y Licencias por Fuente

El sistema maneja con precisión quirúrgica el régimen de propiedad intelectual de cada insumo:

1. **TVN RSS y Medios Nacionales**:
   - *Condición*: Derechos de autor reservados por TVN Media y los medios emisores.
   - *Tratamiento*: Se utilizan exclusivamente titulares, pasajes de contexto y metadatos para fines de indexación interna y asistencia a la sala de redacción, sin republicación no autorizada de piezas completas de terceros.
2. **Banco Mundial Open Data**:
   - *Condición*: Licencia internacional Creative Commons Atribución 4.0 (CC BY 4.0).
   - *Tratamiento*: Cada serie temporal y cifra económica generada en los borradores incorpora el indicador exacto (`NY.GDP.MKTP.KD.ZG`, etc.), país de referencia y atribución formal a la fuente.
3. **USGS Earthquake Data**:
   - *Condición*: Dominio público del Gobierno de los Estados Unidos.
   - *Tratamiento*: Uso abierto de coordenadas geográficas, magnitudes e hipervínculos de evento con fines de alerta ciudadana.
4. **GDELT Project**:
   - *Condición*: Datos abiertos para investigación global y análisis computacional de medios.
   - *Tratamiento*: Empleado como señal de contexto y volumen de cobertura mediática.

---

## 4. Privacidad y Protección de Datos Personales (PII)

- **Datos No Sensibles**: El corpus se compone exclusivamente de hechos de interés público, despachos noticiosos emitidos en abierto, series macroeconómicas de libre acceso y catálogos sismológicos oficiales.
- **Cero Datos Privados**: No se recolectan, almacenan ni procesan datos personales crediticios, cuentas bancarias, historiales médicos ni identificadores de personas privadas protegidos por la Ley 81 de Protección de Datos Personales de Panamá.

---

## 5. Delimitación Explícita Fuera de Alcance (Banca y Finanzas)

En la extensión modular para el sector bancario (CU-05):
- **Finalidad Exclusiva**: Monitoreo de entorno macroeconómico (PIB, inflación) e incidencias logísticas del Canal de Panamá para análisis de riesgo sectorial agregado.
- **Prohibiciones Explícitas**:
  - Queda terminantemente prohibido utilizar el copiloto para automatizar decisiones de concesión o denegación de créditos.
  - Queda prohibido el scoring crediticio de personas naturales o jurídicas individuales.
  - La herramienta provee resúmenes informativos y preguntas para el analista humano de riesgo; no emite dictámenes financieros vinculantes.
