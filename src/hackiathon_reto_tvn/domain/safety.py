"""Safety, Anti-Injection, and Anti-Hallucination Guardrails.

Rules enforced:
1. Anti-injection: Source text is strictly DATA, never INSTRUCTION.
   Malicious payloads attempting to hijack instructions or reveal secrets are sanitized.
2. Anti-hallucination: Reject factual assertions with no registered citation or with content terms
   absent from cited excerpts; abstain when evidence is missing (T06).
3. Citation support: Strict mode checks registered IDs, quoted passages, and conservative lexical containment.
   This lexical filter does not establish semantic entailment.
4. Independent verification: Replicated news wire/agency counts as a single provenance (T02).
"""

import re
import unicodedata
from typing import List, Tuple

from hackiathon_reto_tvn.domain.models import Afirmacion, TipoAfirmacion


class SafetyGuard:
    """Security and compliance shields for AI engineering copilot."""

    # Common prompt injection and adversarial manipulation patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"ignora\s+(todas\s+las\s+)?instrucciones\s+(previas|anteriores)",
        r"system\s+(prompt|alert)",
        r"override\s+(safety\s+)?instructions",
        r"disregard\s+(all\s+)?(limits|instructions|rules)",
        r"revela\s+(el\s+)?(prompt|secreto|clave|token|credencial)",
        r"reveal\s+(the\s+)?(prompt|secret|api[\s_-]?key|credentials)",
        r"forget\s+all\s+rules",
        r"olvida\s+todas\s+las\s+reglas",
        r"you\s+are\s+now\s+an\s+unrestricted",
        r"ahora\s+eres\s+un\s+modelo\s+sin\s+restricciones",
        r"act\s+as\s+dan",
        r"modo\s+desarrollador",
        r"olv[ií]date\s+de\s+.*\s+y\s+act[uú]a\s+como",
        r"afirma\s+(categóricamente|sin\s+pruebas).*\b(fraude|culpab|delito)",
        r"declar[aá](ndolas|ndolos)?\s+formalmente\s+culpables?",
        r"publica\s+inmediatamente\s+.*\s+sin\s+(pasar\s+por\s+)?revisi[oó]n",
        r"drop\s+table|select\s+\*\s+from",
        r"recomienda\s+comprar\s+acciones|garantizando\s+rentabilidad",
        r"liquidity\s+insolvency|quiebra\s+bancaria",
        r"simula\s+que|detalles\s+inventados|paywall",
    ]

    # Function words and attribution boilerplate do not add factual content to a quotation.
    SUPPORT_NONFACTUAL_TOKENS = {
        "a",
        "al",
        "ante",
        "bajo",
        "con",
        "contra",
        "de",
        "del",
        "desde",
        "durante",
        "e",
        "el",
        "ella",
        "en",
        "entre",
        "era",
        "es",
        "esa",
        "ese",
        "esta",
        "este",
        "fue",
        "ha",
        "han",
        "la",
        "las",
        "le",
        "lo",
        "los",
        "mas",
        "más",
        "o",
        "para",
        "por",
        "que",
        "se",
        "segun",
        "según",
        "sin",
        "sobre",
        "su",
        "sus",
        "un",
        "una",
        "uno",
        "unos",
        "unas",
        "y",
        "reporta",
        "informo",
        "informó",
        "indica",
        "indico",
        "indicó",
        "anuncia",
        "anuncio",
        "anunció",
        "afirma",
        "afirmo",
        "afirmó",
        "senala",
        "señala",
        "senaló",
        "señalo",
        "titular",
        "fuente",
        "fuentes",
        "noticia",
        "reportado",
        "reportada",
        "recibido",
        "recibida",
    }

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

    @classmethod
    def validate_citation_support(
        cls,
        afirmaciones: List[Afirmacion],
        valid_source_ids: set[str],
        source_passages: dict[str, List[str]],
    ) -> Tuple[float, List[str]]:
        """Checks citation IDs and conservatively rejects claim tokens absent from cited passages.

        This lexical containment check is a fail-closed guard, not semantic entailment or
        independent verification of the source's truthfulness.
        """
        factual_types = {TipoAfirmacion.HECHO, TipoAfirmacion.DECLARACION}
        total_factual = 0
        supported = 0
        violations: List[str] = []

        for afirmacion in afirmaciones:
            if afirmacion.tipo not in factual_types:
                continue
            total_factual += 1
            if not afirmacion.citas:
                violations.append(f"Afirmación '{afirmacion.id_afirmacion}' carece de citas de evidencia.")
                continue

            cited_tokens: set[str] = set()
            invalid_citation = False
            for cita in afirmacion.citas:
                if cita.id_fuente not in valid_source_ids:
                    violations.append(
                        f"Afirmación '{afirmacion.id_afirmacion}' referencia fuente desconocida '{cita.id_fuente}'."
                    )
                    invalid_citation = True
                    continue

                passages = source_passages.get(cita.id_fuente, [])
                quote = cls._normalize_evidence_text(cita.texto_sustento)
                matching_passage = next(
                    (passage for passage in passages if quote and quote in cls._normalize_evidence_text(passage)),
                    None,
                )
                if matching_passage is None:
                    violations.append(
                        f"Afirmación '{afirmacion.id_afirmacion}' cita un pasaje no encontrado en '{cita.id_fuente}'."
                    )
                    invalid_citation = True
                    continue
                cited_tokens.update(cls._factual_tokens(cita.texto_sustento))

            unsupported_tokens = cls._factual_tokens(afirmacion.texto) - cited_tokens
            if unsupported_tokens:
                violations.append(
                    f"Afirmación '{afirmacion.id_afirmacion}' contiene términos ausentes de los pasajes citados: "
                    f"{', '.join(sorted(unsupported_tokens))}."
                )
                invalid_citation = True

            if not invalid_citation:
                supported += 1

        coverage = supported / total_factual if total_factual else 1.0
        return coverage, violations

    @classmethod
    def _factual_tokens(cls, text: str) -> set[str]:
        normalized = cls._normalize_evidence_text(text)
        return {token for token in re.findall(r"[a-z0-9]+", normalized) if token not in cls.SUPPORT_NONFACTUAL_TOKENS}

    @staticmethod
    def _normalize_evidence_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.casefold())
        return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).split())

    @staticmethod
    def format_explicit_abstention(topic_or_query: str, missing_reason: str) -> str:
        """Generates standard explicit abstention text when corpus has no evidence (T06)."""
        return (
            f"[ABSTENCIÓN EXPLÍCITA]: No existe evidencia verificable en el corpus congelado "
            f"sobre: '{topic_or_query}'.\n"
            f"Razón: {missing_reason}.\n"
            f"Acción recomendada: Abstenerse de publicar o inferir cifras; solicitar verificación de campo o fuente oficial."
        )
