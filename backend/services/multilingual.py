"""Multilingual round-trip orchestration around the frozen agent core.

Phase 9, Plan 01 (D-01 Hindi first-class, D-03 full round-trip): the English
agent core in ``services/agent.py`` is FROZEN — this module only wraps its
inputs (translate query to English) and outputs (translate reply back),
deriving ``alert_level`` from the pre-translation English reply via the
existing ``_derive_alert_level`` helper so translation can never corrupt it
(T-09-02). ``numerals_format`` is pinned to ``international`` in the
translate client so digits survive byte-identical (T-09-02).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services import agent as agent_module
from services.sarvam_client import translate_text

DEFAULT_LANGUAGE = "en-IN"

# D-01 six-language set (canonical BCP-47 codes, shared with the route).
SUPPORTED_LANGUAGES = ("hi-IN", "mr-IN", "ta-IN", "te-IN", "bn-IN", "as-IN")


def normalize_language(language: Optional[str]) -> str:
    """Strip plus lowercase-compare a raw language value (T-09-01)."""
    return (language or DEFAULT_LANGUAGE).strip().lower()


def is_supported(language: Optional[str]) -> bool:
    """True for en-IN (passthrough) and the six D-01 codes."""
    normalized = normalize_language(language)
    return normalized == DEFAULT_LANGUAGE.lower() or normalized in (
        code.lower() for code in SUPPORTED_LANGUAGES
    )


def canonical_language(language: Optional[str]) -> str:
    """Return the canonical BCP-47 code for a supported value.

    Matching is case-insensitive but the returned code keeps canonical
    casing (``HI-in`` -> ``hi-IN``). Raises ``ValueError`` for unknown
    codes; the route turns that into the honest English reply (D-02).
    """
    normalized = normalize_language(language)
    if normalized == DEFAULT_LANGUAGE.lower():
        return DEFAULT_LANGUAGE
    for code in SUPPORTED_LANGUAGES:
        if normalized == code.lower():
            return code
    raise ValueError(
        "Unsupported language. Supported codes: "
        + " ".join(SUPPORTED_LANGUAGES)
        + "."
    )


def process_multilingual_chat(
    message: str, location: Optional[str] = None, language: Optional[str] = None
) -> Dict[str, Any]:
    """Run the hi-IN (or sibling-language) round-trip around the frozen core.

    English (or absent) language short-circuits to ``process_chat`` untouched.
    Otherwise: translate query to ``en-IN`` -> call the frozen
    ``process_chat`` with the English text -> derive ``alert_level`` from the
    English reply BEFORE back-translation -> translate the full English reply
    back to the user's language. Location passes through untouched.

    Returns:
        Dict with keys ``reply`` (translated text), ``alert_level``
        (derived pre-translation), and ``language`` (canonical code).
    """
    canonical = canonical_language(language)
    if canonical == DEFAULT_LANGUAGE:
        result = agent_module.process_chat(message, location)
        return {
            "reply": result["reply"],
            "alert_level": result.get("alert_level", "Green"),
            "language": DEFAULT_LANGUAGE,
        }

    english_query = translate_text(message, canonical, "en-IN")
    result = agent_module.process_chat(english_query, location)
    english_reply = result["reply"]
    # Derive BEFORE back-translation so translation can never corrupt it.
    alert_level = agent_module._derive_alert_level(english_reply)
    translated_reply = translate_text(english_reply, "en-IN", canonical)
    return {
        "reply": translated_reply,
        "alert_level": alert_level,
        "language": canonical,
    }
