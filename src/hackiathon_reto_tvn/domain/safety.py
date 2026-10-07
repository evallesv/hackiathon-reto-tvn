"""Safety, Anti-Injection, and Anti-Hallucination Guardrails.

Rules enforced:
1. Anti-injection: Source text is strictly DATA, never INSTRUCTION.
   Malicious payloads attempting to hijack instructions or reveal secrets are sanitized.
2. Anti-hallucination: Zero tolerance for unsourced facts, quotes, or numbers.
   Explicit abstention when evidence is absent (T06).
3. Citation validation: 100% of factual assertions must map to a registered evidence ID.
4. Independent verification: Replicated news wire/agency counts as a single provenance (T02).
"""

import re
from typing import List, Tuple

from hackiathon_reto_tvn.domain.models import Afirmacion, TipoAfirmacion


class SafetyGuard:
    """Security and compliance shields for AI engineering copilot."""

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"ignora\s+(todas\s+las\s+)?instrucciones\s+(previas|anteriores)",
        r"system\s+prompt",
        r"revela\s+(el\s+)?(prompt|secreto|clave|token)",
        r"reveal\s+(the\s+)?(prompt|secret|api[\s_-]?key)",
        r"forget\s+all\s+rules",
        r"olvida\s+todas\s+las\s+reglas",
        r"you\s+are\s+now\s+an\s+unrestricted",
        r"ahora\s+eres\s+un\s+modelo\s+sin\s+restricciones",
        r"act\s+as\s+dan",
        r"modo\s+desarrollador",
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> Tuple[str, bool]:
        """Sanitizes untrusted source text to treat it as data only.

        Returns (sanitized_text, was_injection_detected).
        """
        detected = False
        cleaned = text

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                detected = True
                cleaned = re.sub(
                    pattern,
                    "[CONTENIDO_BLOQUEADO: INTENTO DE INYECCIÓN DE PROMPT DETECTADO]",
                    cleaned,
                    flags=re.IGNORECASE,
                )

        return cleaned, detected

    @classmethod
    def format_as_data_payload(cls, source_id: str, title: str, content: str) -> str:
        """Encloses source text into an untrusted XML data block with explicit isolation."""
        sanitized_content, content_flagged = cls.sanitize_untrusted_text(content)
        sanitized_title, title_flagged = cls.sanitize_untrusted_text(title)
        flagged = content_flagged or title_flagged
        warning = "\n<!-- ADVERTENCIA: CONTENIDO CON POSIBLE INTENTO DE INYECCIÓN DETECTADO -->" if flagged else ""

        return (
            f'<source_data id="{cls._neutralize_tags(source_id)}">'
            f"{warning}\n"
            f"<title>{cls._neutralize_tags(sanitized_title)}</title>\n"
            f"<content>\n{cls._neutralize_tags(sanitized_content)}\n</content>\n"
            f"</source_data>"
        )

    @staticmethod
    def _neutralize_tags(text: str) -> str:
        """Prevents untrusted text from closing or forging isolation tags (tag breakout)."""
        return re.sub(r"<(/?)(source_data|title|content)\b", r"&lt;\1\2", text, flags=re.IGNORECASE)

    @staticmethod
    def validate_citation_coverage(
        afirmaciones: List[Afirmacion],
        valid_source_ids: set[str],
    ) -> Tuple[float, List[str]]:
        """Validates that 100% of factual assertions have an identifiable citation.

        Returns:
            (coverage_ratio, list_of_violations)
        """
        factual_types = {TipoAfirmacion.HECHO, TipoAfirmacion.DECLARACION}
        total_factual = 0
        validly_cited = 0
        violations: List[str] = []

        for af in afirmaciones:
            if af.tipo in factual_types:
                total_factual += 1
                if not af.citas:
                    violations.append(
                        f"Afirmación '{af.id_afirmacion}' de tipo {af.tipo.value} carece de citas de evidencia."
                    )
                    continue

                # Check that all citations refer to valid sources
                all_valid = True
                for c in af.citas:
                    if c.id_fuente not in valid_source_ids:
                        violations.append(
                            f"Afirmación '{af.id_afirmacion}' referencia fuente desconocida '{c.id_fuente}'."
                        )
                        all_valid = False
                if all_valid:
                    validly_cited += 1

        coverage = (validly_cited / total_factual) if total_factual > 0 else 1.0
        return coverage, violations

    @staticmethod
    def format_explicit_abstention(topic_or_query: str, missing_reason: str) -> str:
        """Generates standard explicit abstention text when corpus has no evidence (T06)."""
        return (
            f"[ABSTENCIÓN EXPLÍCITA]: No existe evidencia verificable en el corpus congelado "
            f"sobre: '{topic_or_query}'.\n"
            f"Razón: {missing_reason}.\n"
            f"Acción recomendada: Abstenerse de publicar o inferir cifras; solicitar verificación de campo o fuente oficial."
        )
