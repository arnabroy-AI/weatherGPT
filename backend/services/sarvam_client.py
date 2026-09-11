"""Sarvam translate thin client (Phase 9, Plan 01 — translate only).

Synchronous httpx client pinned to model ``mayura:v1`` per the Sarvam Mayura
docs page (11-language set, 1000 characters per request, header
``api-subscription-key``, JSON keys ``input`` / ``source_language_code`` /
``target_language_code``, response key ``translated_text``).

Security posture (T-09-03):
- The ``SARVAM_API_KEY`` value is only ever placed on the outbound header;
  it is never logged, never printed, and never embedded in an exception
  message. Failures are logged server-side via ``logger.exception`` and
  surfaced as sanitized ``RuntimeError`` values the route maps to 502.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)

TRANSLATE_URL = "https://api.sarvam.ai/translate"
TRANSLATE_MODEL = "mayura:v1"
REQUEST_TIMEOUT_SECONDS = 15.0

# Sarvam translate rejects inputs longer than 1000 characters per request
# (T-09-04); overlong inputs are split at sentence boundaries instead.
MAX_CHARS_PER_REQUEST = 1000

# Module-level transport override for tests (httpx.MockTransport), mirroring
# the tools/imd_client.py set_transport pattern. Production leaves this None.
_TRANSPORT_OVERRIDE: Optional[httpx.BaseTransport] = None


def set_transport(transport: Optional[httpx.BaseTransport]) -> None:
    """Pin a transport (e.g. httpx.MockTransport) for tests; None restores live."""
    global _TRANSPORT_OVERRIDE
    _TRANSPORT_OVERRIDE = transport


def reset_transport() -> None:
    """Clear any test transport override."""
    set_transport(None)


def _split_into_chunks(text: str, limit: int = MAX_CHARS_PER_REQUEST) -> List[str]:
    """Split text at sentence boundaries into ordered sub-limit chunks.

    Sentences are cut after ``.`` / ``!`` / ``?`` / Devanagari danda ``।``
    / newline followed by whitespace. A single overlong sentence with no
    boundary is hard-split at the limit so no request ever exceeds it.
    Inputs within the limit are returned untouched (byte-identical, no
    whitespace normalization) so short queries and replies pass through
    exactly as written.
    """
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[.!?\u0964\n])\s+", text.strip())
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        while len(sentence) > limit:
            # Flush any accumulated chunk, then carve the long sentence.
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:limit])
            sentence = sentence[limit:]
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks or [text]


def _post_translate(
    text: str,
    source_language_code: str,
    target_language_code: str,
    api_key: str,
    transport: Optional[httpx.BaseTransport],
) -> str:
    """POST one sub-1000-character chunk; return its translated_text."""
    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "model": TRANSLATE_MODEL,
        "numerals_format": "international",
    }
    headers = {"api-subscription-key": api_key}
    try:
        with httpx.Client(
            transport=transport, timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = client.post(TRANSLATE_URL, json=payload, headers=headers)
    except Exception as exc:
        logger.exception("Sarvam translate request failed")
        raise RuntimeError("Sarvam translate failure: upstream request failed.") from exc
    if response.status_code != 200:
        logger.exception(
            "Sarvam translate returned non-200 status=%s", response.status_code
        )
        raise RuntimeError(
            "Sarvam translate failure: upstream returned status "
            f"{response.status_code}."
        )
    try:
        translated = response.json().get("translated_text")
    except Exception as exc:
        logger.exception("Sarvam translate returned unparseable JSON")
        raise RuntimeError(
            "Sarvam translate failure: malformed upstream response."
        ) from exc
    if not translated or not isinstance(translated, str):
        logger.exception("Sarvam translate response missing translated_text")
        raise RuntimeError(
            "Sarvam translate failure: malformed upstream response."
        )
    return translated


def translate_text(
    text: str,
    source_language_code: str,
    target_language_code: str,
    transport: Optional[httpx.BaseTransport] = None,
) -> str:
    """Translate text via Sarvam Mayura; return the translated string.

    Args:
        text: Source text (must be non-empty).
        source_language_code: BCP-47 code, e.g. ``hi-IN``.
        target_language_code: BCP-47 code, e.g. ``en-IN``.
        transport: Optional per-call transport override for tests; falls
            back to the module-level override set via :func:`set_transport`.

    Raises:
        ValueError: If ``text`` is empty.
        RuntimeError: Sanitized translate failure (missing key, non-200,
            malformed response). Never carries the API key.
    """
    if not text or not text.strip():
        raise ValueError("text must be a non-empty string.")
    api_key = get_settings().SARVAM_API_KEY
    if not api_key:
        raise RuntimeError(
            "Sarvam translate failure: SARVAM_API_KEY is not configured. "
            "Add it to your `.env` file (see `.env.example`)."
        )
    active_transport = (
        transport if transport is not None else _TRANSPORT_OVERRIDE
    )
    chunks = _split_into_chunks(text)
    translated_chunks = [
        _post_translate(
            chunk, source_language_code, target_language_code, api_key, active_transport
        )
        for chunk in chunks
    ]
    return " ".join(translated_chunks)
