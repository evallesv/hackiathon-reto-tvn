"""Domain models representing data contracts, scoring structures, and entities

for HackIAthon 'De la señal a la decisión'.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Modalidad(str, Enum):
    TVN_EDITORIAL = "tvn_editorial"
    BANCA = "banca"


class EstadoEvidencia(str, Enum):
    INSUFICIENTE = "insuficiente"
    PARCIAL = "parcial"
    SUFICIENTE_PARA_BORRADOR = "suficiente_para_borrador"


class EstadoRevision(str, Enum):
    NUEVO = "nuevo"
    EN_REVISION = "en_revision"
    REQUIERE_EVIDENCIA = "requiere_evidencia"
    APROBADO_COMO_BORRADOR = "aprobado_como_borrador"
    DESCARTADO = "descartado"


class RangoPuntaje(str, Enum):
    BAJO = "bajo"  # [0, 40)
    MEDIO = "medio"  # [40, 70)
    ALTO = "alto"  # [70, 100]


class TipoAfirmacion(str, Enum):
    HECHO = "hecho"
    DECLARACION = "declaracion"
    INFERENCIA = "inferencia"
    HIPOTESIS = "hipotesis"


class Noticia(BaseModel):
    """Contrato de datos para noticias.csv."""

    id_noticia: str
    titulo: str
    url: str
    medio: str
    idioma: str = "es"
    fecha_publicacion: str
    fecha_deteccion: str
    fecha_extraccion: str
    tema: str
    origen: str
    alcance_texto: str = "titular_metadatos"


class Indicador(BaseModel):
    """Contrato de datos para indicadores.csv (Banco Mundial / SBP)."""

    pais_iso3: str
    indicador_id: str
    anio: int
    valor: Optional[float] = None
    unidad: str
    fuente_url: str
    fecha_extraccion: str
    licencia: str = "CC BY 4.0"


class EventoGeoJSON(BaseModel):
    """Contrato de datos para eventos.geojson (USGS)."""

    id: str
    magnitude: float
    time: int
    updated: int
    longitude: float
    latitude: float
    depth: float
    place: str
    status: str
    url: str


class ComponentesPuntaje(BaseModel):
    """Componentes normalizados en [0.0, 1.0]."""

    relevancia: float = Field(ge=0.0, le=1.0, description="R: Relación con Panamá y temática (peso 30)")
    impacto_potencial: float = Field(ge=0.0, le=1.0, description="I: Interés público o alcance sectorial (peso 25)")
    urgencia: float = Field(ge=0.0, le=1.0, description="U: Tiempo disponible para actuar (peso 20)")
    novedad: float = Field(ge=0.0, le=1.0, description="N: Diferencia frente a eventos ya agrupados (peso 15)")
    evidencia_disponible: float = Field(ge=0.0, le=1.0, description="E: Fuentes pertinentes e identificables (peso 10)")


class PuntajeAtencion(BaseModel):
    """Puntaje de atención total calculado P = 30R + 25I + 20U + 15N + 10E."""

    valor_total: float = Field(ge=0.0, le=100.0)
    rango: RangoPuntaje
    componentes: ComponentesPuntaje
    formula_aplicada: str = "P = 30R + 25I + 20U + 15N + 10E"
    version_reglas: str = "v1.0"
    justificacion: str = ""


class CitaEvidencia(BaseModel):
    """Cita trazable vinculada a una evidencia verificable."""

    id_fuente: str
    campo_o_pasaje: str
    texto_sustento: str
    url_fuente: Optional[str] = None


class Afirmacion(BaseModel):
    """Afirmación catalogada distinguiendo hechos, declaraciones, inferencias e hipótesis."""

    id_afirmacion: str
    texto: str
    tipo: TipoAfirmacion
    citas: list[CitaEvidencia] = Field(default_factory=list)


class BorradorEditorial(BaseModel):
    """Entregable para TVN Media."""

    titulo_propuesto: str
    brief_250: str
    enfoque_interes_publico: str
    preguntas_investigacion: list[str] = Field(min_length=3, max_length=5)
    fuentes_pendientes: list[str] = Field(default_factory=list)
    guion_45_60s: str
    copy_digital_80: str
    afirmaciones: list[Afirmacion] = Field(default_factory=list)
    basado_unicamente_en_titular_metadatos: bool = True


class BorradorBancario(BaseModel):
    """Entregable para sector bancario."""

    resumen_250: str
    sectores_relacionados: list[str] = Field(default_factory=list)
    horizonte_temporal: str
    evidencia: list[str] = Field(default_factory=list)
    preguntas_analista: list[str] = Field(min_length=3, max_length=5)
    observacion: str
    hipotesis_impacto: str
    afirmaciones: list[Afirmacion] = Field(default_factory=list)


class FichaCaso(BaseModel):
    """Contrato de datos para fichas.jsonl."""

    id_caso: str
    modalidad: Modalidad = Modalidad.TVN_EDITORIAL
    ids_fuente: list[str] = Field(default_factory=list)
    afirmaciones: list[Afirmacion] = Field(default_factory=list)
    citas: list[CitaEvidencia] = Field(default_factory=list)
    puntaje: float
    componentes: ComponentesPuntaje
    estado_evidencia: EstadoEvidencia
    borrador: dict[str, Any] = Field(default_factory=dict)
    estado_revision: EstadoRevision = EstadoRevision.NUEVO
    persona_revisora: Optional[str] = None
    fecha_creacion: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observaciones_revision: Optional[str] = None


class ManifestItem(BaseModel):
    archivo: str
    cantidad_registros: int
    licencia: str
    sha256: str
    transformaciones: str


class Manifest(BaseModel):
    version: str = "v1.0"
    fecha_corte_utc: str
    consultas: list[str]
    cantidad_por_archivo: dict[str, int]
    licencia_condiciones: str
    archivos: list[ManifestItem]
