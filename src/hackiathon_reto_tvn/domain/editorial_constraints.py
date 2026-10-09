"""Deterministic length and speaking-time checks for generated editorial deliverables."""

import math
import re

from hackiathon_reto_tvn.domain.models import BorradorBancario, BorradorEditorial

_WORD_PATTERN = re.compile(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+(?:['’][\wáéíóúüñÁÉÍÓÚÜÑ]+)*\b")


def count_words(value: str) -> int:
    """Count words consistently across Spanish text, punctuation and hyphenated tokens."""
    return len(_WORD_PATTERN.findall(value))


def validate_editorial_draft(
    draft: BorradorEditorial,
    brief_word_limit: int,
    copy_word_limit: int,
    script_min_seconds: int,
    script_max_seconds: int,
    script_words_per_minute: int,
) -> list[str]:
    """Return concrete violations of the official TVN brief, copy and script length limits."""
    violations: list[str] = []
    brief_words = count_words(draft.brief_250)
    if brief_words > brief_word_limit:
        violations.append(f"brief: {brief_words} palabras; máximo {brief_word_limit}")

    copy_words = count_words(draft.copy_digital_80)
    if copy_words > copy_word_limit:
        violations.append(f"copy digital: {copy_words} palabras; máximo {copy_word_limit}")

    script_words = count_words(draft.guion_45_60s)
    minimum_words = math.ceil(script_min_seconds * script_words_per_minute / 60)
    maximum_words = math.floor(script_max_seconds * script_words_per_minute / 60)
    if not minimum_words <= script_words <= maximum_words:
        violations.append(
            f"guion: {script_words} palabras; para {script_min_seconds}–"
            f"{script_max_seconds} s a {script_words_per_minute} palabras/min se requieren "
            f"{minimum_words}–{maximum_words}"
        )
    return violations


def validate_banking_draft(draft: BorradorBancario, summary_word_limit: int) -> list[str]:
    """Return violations of the banking bulletin's configured summary limit."""
    summary_words = count_words(draft.resumen_250)
    if summary_words > summary_word_limit:
        return [f"resumen bancario: {summary_words} palabras; máximo {summary_word_limit}"]
    return []
