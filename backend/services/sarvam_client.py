"""Sarvam thin client (Phase 9 — translate plus STT plus TTS).

Model pins per D-02 (Claude's Discretion, verified against the Sarvam docs
page set at plan time):
- Translate: ``mayura:v1`` for hi-IN / mr-IN / ta-IN / te-IN / bn-IN (1000
  characters per request, ``numerals_format: international``);
  ``sarvam-translate:v1`` whenever as-IN sits on either side of the pair
  (covers all 22 scheduled languages, 2000 characters per request).
- STT: ``saaras:v3`` on ``/speech-to-text`` with ``mode: transcribe``
  (23-language Saaras set including as-IN; 30-second real-time REST cap —
  enforced locally as a 2MB byte bound at the voice route per T-09-05).
- TTS: ``bulbul:v3`` with speaker ``shubh`` on ``/text-to-speech``
  (11-language Bulbul set with NO as-IN entry — as-IN TTS stays an honest
  422, never silent substitution, per D-02).

Security posture (T-09-03, T-09-08):
- The ``SARVAM_API_KEY`` value is only ever placed on the outbound
  ``api-subscription-key`` header; it is never logged, never printed, and
  never embedded in an exception message. Failures are logged server-side
  via ``logger.exception`` and surfaced as sanitized ``RuntimeError`` values
  the routes map to 502.
"""

from __future__ import annotations

import base64
import logging
import re
from typing import Dict, List, Optional, Tuple

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)

TRANSLATE_URL = "https://api.sarvam.ai/translate"
TRANSLATE_MODEL = "mayura:v1"
# Assamese either side routes here (all 22 scheduled languages).
AS_TRANSLATE_MODEL = "sarvam-translate:v1"
REQUEST_TIMEOUT_SECONDS = 15.0

# Sarvam Mayura rejects inputs longer than 1000 characters per request
# (T-09-04); overlong inputs are split at sentence boundaries instead.
MAX_CHARS_PER_REQUEST = 1000
# Sarvam Translate allows longer inputs per request than Mayura.
MAX_CHARS_SARVAM_TRANSLATE = 2000

# Saaras speech-to-text pin (D-02): 23-language set including as-IN.
STT_URL = "https://api.sarvam.ai/speech-to-text"
STT_MODEL = "saaras:v3"
STT_MODE = "transcribe"

# Bulbul text-to-speech pin (D-02): 11-language set, no as-IN entry.
TTS_URL = "https://api.sarvam.ai/text-to-speech"
TTS_MODEL = "bulbul:v3"
TTS_SPEAKER = "shubh"

# Per-language capability map (D-02): gates every translate, STT, and TTS
# call so unsupported combinations never reach the provider.
CAPABILITIES: Dict[str, Dict[str, object]] = {
    "hi-IN": {"translate_model": TRANSLATE_MODEL, "stt_supported": True, "tts_supported": True},
    "mr-IN": {"translate_model": TRANSLATE_MODEL, "stt_supported": True, "tts_supported": True},
    "ta-IN": {"translate_model": TRANSLATE_MODEL, "stt_supported": True, "tts_supported": True},
    "te-IN": {"translate_model": TRANSLATE_MODEL, "stt_supported": True, "tts_supported": True},
    "bn-IN": {"translate_model": TRANSLATE_MODEL, "stt_supported": True, "tts_supported": True},
    "as-IN": {"translate_model": AS_TRANSLATE_MODEL, "stt_supported": True, "tts_supported": False},
}

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


def _active_transport(transport: Optional[httpx.BaseTransport]) -> Optional[httpx.BaseTransport]:
    """Per-call override wins; otherwise fall back to the module override."""
    return transport if transport is not None else _TRANSPORT_OVERRIDE


def _require_api_key() -> str:
    """Return the configured key or raise a sanitized RuntimeError."""
    api_key = get_settings().SARVAM_API_KEY
    if not api_key:
        raise RuntimeError(
            "Sarvam translate failure: SARVAM_API_KEY is not configured. "
            "Add it to your `.env` file (see `.env.example`)."
        )
    return api_key


def capability_for(language_code: Optional[str]) -> Optional[Dict[str, object]]:
    """Case-insensitive lookup in the D-02 capability map; None when unknown."""
    normalized = (language_code or "").strip().lower()
    for code, caps in CAPABILITIES.items():
        if normalized == code.lower():
            return caps
    return None


def translate_model_for(source_language_code: str, target_language_code: str) -> str:
    """Pick the translate model for a pair: as-IN either side routes to
    ``sarvam-translate:v1``; every other pair stays on ``mayura:v1``."""
    pair = {
        (source_language_code or "").strip().lower(),
        (target_language_code or "").strip().lower(),
    }
    if "as-in" in pair:
        return AS_TRANSLATE_MODEL
    return TRANSLATE_MODEL


def _chunk_limit_for_model(model: str) -> int:
    """Per-model request size bound: 2000 for sarvam-translate, else 1000."""
    if model == AS_TRANSLATE_MODEL:
        return MAX_CHARS_SARVAM_TRANSLATE
    return MAX_CHARS_PER_REQUEST


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
    model: str,
) -> str:
    """POST one chunk with the given model; return its translated_text."""
    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "model": model,
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
    """Translate text via Sarvam; return the translated string.

    Model routing (D-02): pairs with as-IN on either side use
    ``sarvam-translate:v1`` (2000-char chunks); all other pairs use
    ``mayura:v1`` (1000-char chunks).

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
    api_key = _require_api_key()
    active_transport = _active_transport(transport)
    model = translate_model_for(source_language_code, target_language_code)
    chunks = _split_into_chunks(text, _chunk_limit_for_model(model))
    translated_chunks = [
        _post_translate(
            chunk, source_language_code, target_language_code, api_key, active_transport, model
        )
        for chunk in chunks
    ]
    return " ".join(translated_chunks)


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    language_code: str = "unknown",
    transport: Optional[httpx.BaseTransport] = None,
) -> Tuple[str, str]:
    """Transcribe audio via Saaras STT; return ``(transcript, language_code)``.

    Posts multipart ``file`` plus model ``saaras:v3`` plus ``language_code``
    plus ``mode: transcribe`` to ``/speech-to-text``. ``language_code`` of
    ``"unknown"`` lets the provider detect the language; the detected code
    is echoed back as the second tuple element.

    Raises:
        ValueError: If ``audio_bytes`` is empty.
        RuntimeError: Sanitized STT failure (missing key, non-200,
            malformed response). Never carries the API key.
    """
    if not audio_bytes:
        raise ValueError("audio_bytes must be non-empty.")
    api_key = _require_api_key()
    active_transport = _active_transport(transport)
    safe_filename = filename or "audio.wav"
    files = {"file": (safe_filename, audio_bytes)}
    data = {
        "model": STT_MODEL,
        "language_code": language_code or "unknown",
        "mode": STT_MODE,
    }
    headers = {"api-subscription-key": api_key}
    try:
        with httpx.Client(
            transport=active_transport, timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = client.post(STT_URL, files=files, data=data, headers=headers)
    except Exception as exc:
        logger.exception("Sarvam STT request failed")
        raise RuntimeError("Sarvam STT failure: upstream request failed.") from exc
    if response.status_code != 200:
        logger.exception("Sarvam STT returned non-200 status=%s", response.status_code)
        raise RuntimeError(
            "Sarvam STT failure: upstream returned status "
            f"{response.status_code}."
        )
    try:
        body = response.json()
    except Exception as exc:
        logger.exception("Sarvam STT returned unparseable JSON")
        raise RuntimeError(
            "Sarvam STT failure: malformed upstream response."
        ) from exc
    transcript = body.get("transcript") if isinstance(body, dict) else None
    if not transcript or not isinstance(transcript, str):
        logger.exception("Sarvam STT response missing transcript")
        raise RuntimeError("Sarvam STT failure: malformed upstream response.")
    detected = body.get("language_code") or language_code or "unknown"
    return transcript, detected


def synthesize_speech(
    text: str,
    language_code: str,
    transport: Optional[httpx.BaseTransport] = None,
) -> bytes:
    """Synthesize speech via Bulbul TTS; return raw audio bytes.

    Posts JSON ``text`` / ``language_code`` / model ``bulbul:v3`` / speaker
    ``shubh`` to ``/text-to-speech`` and returns the base64-decoded first
    entry of the ``audios`` array. Callers gate as-IN before calling (Bulbul
    has no as-IN voice — honest 422, never silent substitution).

    Raises:
        ValueError: If ``text`` is empty.
        RuntimeError: Sanitized TTS failure (missing key, non-200,
            malformed response). Never carries the API key.
    """
    if not text or not text.strip():
        raise ValueError("text must be a non-empty string.")
    api_key = _require_api_key()
    active_transport = _active_transport(transport)
    payload = {
        "text": text,
        "language_code": language_code,
        "model": TTS_MODEL,
        "speaker": TTS_SPEAKER,
    }
    headers = {"api-subscription-key": api_key}
    try:
        with httpx.Client(
            transport=active_transport, timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = client.post(TTS_URL, json=payload, headers=headers)
    except Exception as exc:
        logger.exception("Sarvam TTS request failed")
        raise RuntimeError("Sarvam TTS failure: upstream request failed.") from exc
    if response.status_code != 200:
        logger.exception("Sarvam TTS returned non-200 status=%s", response.status_code)
        raise RuntimeError(
            "Sarvam TTS failure: upstream returned status "
            f"{response.status_code}."
        )
    try:
        body = response.json()
    except Exception as exc:
        logger.exception("Sarvam TTS returned unparseable JSON")
        raise RuntimeError(
            "Sarvam TTS failure: malformed upstream response."
        ) from exc
    audios = body.get("audios") if isinstance(body, dict) else None
    if not audios or not isinstance(audios, list) or not audios[0]:
        logger.exception("Sarvam TTS response missing audios")
        raise RuntimeError("Sarvam TTS failure: malformed upstream response.")
    try:
        return base64.b64decode(audios[0])
    except Exception as exc:
        logger.exception("Sarvam TTS returned undecodable audio payload")
        raise RuntimeError("Sarvam TTS failure: malformed upstream response.") from exc
