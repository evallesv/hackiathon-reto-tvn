# ADR-0011: Almacenamiento Persistente SQLite en Fly.io Volumes e Ingesta Periódica de Fuentes Vivas

* **Estado**: Aceptado
* **Fecha**: 2026-10-06
* **Decisores**: Equipo de Ingeniería de IA

## Contexto

El copiloto editorial y bancario opera inicialmente sobre un corpus congelado offline (`data/raw/`) para garantizar la auditabilidad del jurado y la prueba de contingencia **T10** ("Sin internet durante la demo"). Sin embargo, en un entorno de producción continuo, el sistema debe ser capaz de enriquecerse de manera autónoma y periódica a partir de las fuentes oficiales públicas:
1. RSS en vivo de TVN Panamá (`https://www.tvn-2.com/rss/`).
2. Artículos recientes monitoreados por la API GDELT DOC 2.0.
3. Indicadores macroeconómicos actualizados del Banco Mundial.
4. Catálogo sísmico regional del USGS en tiempo real.

Para persistir estos datos sin depender de bases de datos externas pesadas o con costos adicionales innecesarios, se requiere un mecanismo ligero, embebido, compatible con la arquitectura hexagonal y persistente ante reinicios de máquinas en Fly.io.

## Decisión

1. **Creación de Volúmenes Persistentes en Fly.io (`sentria_data`)**:
   - Se crearon volúmenes de 1 GB cifrados en la región primaria `dfw` (`vol_v3gkpk8z5wm8gwl4` y `vol_v3gkpk8w8j2wzxw4`).
   - Se configuró la sección `[mounts]` en `fly.toml` con destino `/data`.
   - Se pre-creó el directorio `/data` con los permisos del usuario sin privilegios `appuser` en el `Dockerfile`.

2. **Base de Datos Embebida SQLite con Modo WAL**:
   - Se implementó `SQLiteStorage` en `src/hackiathon_reto_tvn/adapters/data/sqlite_storage.py`.
   - Esquema relacional con tablas: `noticias_live`, `indicadores_live`, `eventos_live` e `ingestion_runs`.
   - Concurrencia segura configurada con `PRAGMA journal_mode=WAL;`, `PRAGMA busy_timeout=5000;` y `PRAGMA synchronous=NORMAL;`.
   - Ruta configurable mediante `SQLITE_DB_PATH` (`/data/copilot.db` en producción, `data/storage/copilot.db` localmente).

3. **Mecanismo de Ingesta Periódica**:
   - `LiveDataFetcher` en `src/hackiathon_reto_tvn/adapters/data/live_fetchers.py` que consume de forma asíncrona mediante `httpx` y `feedparser`.
   - `ingestion_scheduler` en `src/hackiathon_reto_tvn/services/ingestion_scheduler.py` que ejecuta ciclos cada $N$ minutos en segundo plano durante el ciclo de vida de FastAPI.
   - Script independiente `scripts/periodic_ingestion.py` y comandos del CLI (`hackiathon-tvn ingest`, `hackiathon-tvn db-status`) para ejecuciones programadas y auditoría.
   - Endpoints de control en API: `GET /api/v1/ingestion/status`, `POST /api/v1/ingestion/trigger`, `GET /api/v1/ingestion/noticias`.

4. **Preservación Hermética del Dataset Congelado**:
   - Las pruebas automatizadas y los tests offline (**T10**) continúan evaluando `data/raw/` de forma inmutable, desactivando automáticamente la ingesta viva (`INGESTION_ENABLED=false`).

## Consecuencias

### Positivas
* **Persistencia Cero Costo**: Los datos sobreviven a reinicios de contenedor y redepiegues en Fly.io gracias a los volúmenes montados.
* **Autonomía Operativa**: El copiloto actualiza noticias, indicadores y sismos de Panamá de manera automática sin intervención manual.
* **Separación de Responsabilidades**: El corpus congelado para el jurado permanece inmutable mientras que la base SQLite captura la actividad viva.
* **Alta Disponibilidad y Resiliencia**: Si alguna API externa falla temporalmente o limita la tasa de peticiones, la ingesta registra el error en `ingestion_runs` sin degradar el servicio principal.
