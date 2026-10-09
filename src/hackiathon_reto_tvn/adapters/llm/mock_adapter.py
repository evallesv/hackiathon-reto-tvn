"""Mock LLM Adapter for deterministic tests, CI runs, and offline demo fallback (T10)."""

import html
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from hackiathon_reto_tvn.domain.models import (
    BorradorBancario,
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
            # Build the offline example from evidence actually present in the isolated prompt.
            source_match = re.search(r'<source_data id="([^"]+)">', prompt)
            title_match = re.search(r"<title>(.*?)</title>", prompt, flags=re.DOTALL)
            if source_match is None or title_match is None:
                raise ValueError("El modo mock requiere una fuente y un titular presentes en el caso.")
            cited_id = source_match.group(1)
            source_title = html.unescape(title_match.group(1)).strip()
            supported_statement = source_title
            data = {
                "titulo_propuesto": "Tema para verificación editorial",
                "brief_250": f"{supported_statement}. No se dispone del artículo completo; los detalles requieren verificación.",
                "enfoque_interes_publico": "Verificar el alcance, contexto y consecuencias con fuentes directas.",
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
                    f"{supported_statement}. El material disponible contiene únicamente el titular y sus metadatos. "
                    "Con esta información no es posible confirmar todavía todos los detalles de la noticia. "
                    "La redacción debe consultar documentos públicos, hablar con las autoridades responsables y "
                    "buscar a las personas directamente afectadas. También corresponde revisar cuándo ocurrió el "
                    "hecho, qué antecedentes ayudan a entenderlo y qué preguntas siguen abiertas. Antes de publicar, "
                    "el equipo verificará cada dato con una fuente identificable y explicará con claridad cualquier "
                    "información que todavía no esté disponible. El titular sirve como punto de partida para la "
                    "investigación, pero no reemplaza el contexto ni la confirmación independiente. En esta etapa, "
                    "las cifras, las causas y las consecuencias deben permanecer pendientes hasta que exista respaldo "
                    "documental suficiente. La audiencia merece conocer qué se sabe, qué falta por comprobar y cómo "
                    "se buscará esa información."
                ),
                "copy_digital_80": f"{supported_statement}. Información basada únicamente en titular y metadatos; contexto pendiente de verificación.",
                "afirmaciones": [
                    {
                        "id_afirmacion": "AF-001",
                        "texto": supported_statement,
                        "tipo": "declaracion",
                        "citas": [
                            {
                                "id_fuente": cited_id,
                                "campo_o_pasaje": "title",
                                "texto_sustento": source_title,
                            }
                        ],
                    }
                ],
                "basado_unicamente_en_titular_metadatos": True,
            }
            return response_model.model_validate(data)

        # Handle BorradorBancario schema specifically (CU-05)
        if response_model == BorradorBancario:
            source_match = re.search(r'<source_data id="([^"]+)">', prompt)
            title_match = re.search(r"<title>(.*?)</title>", prompt, flags=re.DOTALL)
            if source_match is None or title_match is None:
                raise ValueError("El modo mock requiere una fuente y un titular presentes en el caso.")
            cited_id = source_match.group(1)
            source_title = html.unescape(title_match.group(1)).strip()
            supported_statement = source_title
            data_bancaria = {
                "resumen_250": (
                    f"{supported_statement}. La evidencia disponible no demuestra por sí sola un impacto bancario o sectorial."
                ),
                "sectores_relacionados": [],
                "horizonte_temporal": "No determinado por la evidencia disponible",
                "evidencia": [cited_id],
                "preguntas_analista": [
                    "¿Qué fuente oficial permite cuantificar el posible efecto sectorial?",
                    "¿Qué período y unidad deberían usarse para contrastar esta señal?",
                    "¿Qué evidencia independiente permitiría evaluar su alcance?",
                ],
                "observacion": f"{supported_statement}. El titular no confirma consecuencias económicas.",
                "hipotesis_impacto": "Hipótesis pendiente: evaluar si la señal tiene un efecto sectorial con datos oficiales adicionales.",
                "afirmaciones": [
                    {
                        "id_afirmacion": "AF-BANC-001",
                        "texto": supported_statement,
                        "tipo": "declaracion",
                        "citas": [
                            {
                                "id_fuente": cited_id,
                                "campo_o_pasaje": "title",
                                "texto_sustento": source_title,
                            }
                        ],
                    }
                ],
            }
            return response_model.model_validate(data_bancaria)

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
