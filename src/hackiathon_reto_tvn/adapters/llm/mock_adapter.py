"""Mock LLM Adapter for deterministic tests, CI runs, and offline demo fallback (T10)."""

import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from hackiathon_reto_tvn.domain.models import (
    BorradorEditorial,
)
from hackiathon_reto_tvn.domain.safety import SafetyGuard
from hackiathon_reto_tvn.ports.llm_port import BaseLLMClient

T = TypeVar("T", bound=BaseModel)


class MockLLMAdapter(BaseLLMClient):
    """Deterministic LLM connector requiring no API keys or internet connection."""

    def __init__(self, model_name: str = "mock-muse-spark-offline") -> None:
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> str:
        _, injection = SafetyGuard.sanitize_untrusted_text(prompt)
        if injection:
            return (
                "[SEGURIDAD]: Intento de manipulación o inyección de instrucciones detectado. "
                "La fuente se procesa únicamente como dato pasivo no confiable."
            )

        if "inexistente" in prompt.lower() or "sin evidencia" in prompt.lower():
            return SafetyGuard.format_explicit_abstention(
                topic_or_query="Tema solicitado",
                missing_reason="El corpus congelado no contiene registros verificables sobre este hecho",
            )

        return (
            "Análisis editorial generado sobre la base de fuentes públicas verificadas de Panamá. "
            "Todas las afirmaciones se fundamentan en los IDs de evidencia extraídos."
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_instruction: str = "",
        temperature: float = 0.1,
    ) -> T:
        _, injection = SafetyGuard.sanitize_untrusted_text(prompt)

        # Handle BorradorEditorial schema specifically
        if response_model == BorradorEditorial:
            # Cite the first source actually supplied in the prompt (deterministic); legacy fallback NOT-001.
            source_match = re.search(r'<source_data id="([^"]+)">', prompt)
            cited_id = source_match.group(1) if source_match else "NOT-001"
            data = {
                "titulo_propuesto": "Monitoreo de Infraestructura y Servicios en Panamá",
                "brief_250": (
                    "Este brief sintetiza reportes recientes sobre infraestructura y servicios públicos "
                    "en la República de Panamá, contrastados con registros de series oficiales. "
                    "La información se basa exclusivamente en los metadatos y titulares recopilados."
                ),
                "enfoque_interes_publico": "Impacto directo en la movilidad urbana y calidad de servicios para la ciudadanía.",
                "preguntas_investigacion": [
                    "¿Cuál es el calendario oficial de mitigación presentado por las autoridades?",
                    "¿Qué partidas presupuestarias han sido asignadas en el ejercicio fiscal vigente?",
                    "¿Qué porcentaje de la población afectada cuenta con planes de contingencia activos?",
                ],
                "fuentes_pendientes": [
                    "Auditoría de la Contraloría General de la República",
                    "Declaración oficial de la entidad rectora de servicios públicos",
                ],
                "guion_45_60s": (
                    "Autoridades y reportes ciudadanos alertan sobre la necesidad de mantenimiento en vías clave de Panamá. "
                    "Datos oficiales indican que la inversión del sector ha mantenido niveles históricos. "
                    "Un equipo editorial investiga los plazos de entrega comprometidos para la comunidad."
                ),
                "copy_digital_80": (
                    "Monitoreo informativo: Revisamos los hechos verificados sobre infraestructura en Panamá. "
                    "Conoce los datos y lo que falta por confirmar. #Panama #Noticias #TVN"
                ),
                "afirmaciones": [
                    {
                        "id_afirmacion": "AF-001",
                        "texto": "Se reportaron trabajos de mantenimiento programados en la red vial principal.",
                        "tipo": "hecho",
                        "citas": [
                            {
                                "id_fuente": cited_id,
                                "campo_o_pasaje": "titulo",
                                "texto_sustento": "Reporte de trabajos viales en Panamá",
                                "url_fuente": "https://www.tvn-2.com/noticia/1",
                            }
                        ],
                    }
                ],
                "basado_unicamente_en_titular_metadatos": True,
            }
            return response_model.model_validate(data)

        # Generic dummy instance for other Pydantic models
        try:
            return response_model.model_validate({})
        except Exception:
            # Construct minimal mock fields
            fields: dict[str, Any] = {}
            for name, field in response_model.model_fields.items():
                if field.annotation is str:
                    fields[name] = "mock_text"
                elif field.annotation is int:
                    fields[name] = 1
                elif field.annotation is float:
                    fields[name] = 0.5
                elif field.annotation is list:
                    fields[name] = []
                elif field.annotation is dict:
                    fields[name] = {}
            return response_model.model_validate(fields)
