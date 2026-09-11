"""API endpoints (traffic directors — no business logic here)."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from core.config import get_settings
from api.throttle import check_rate_limit
from schemas.alerts import CheckResponse, SendRequest, StatusResponse, SubscribeRequest
from schemas.chat import ChatRequest, ChatResponse, SpeakRequest, TranscribeResponse
from services import alert_watcher, fcm_client
from services.agent import process_chat
from services.multilingual import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    TTS_UNSUPPORTED_MESSAGE,
    canonical_language,
    normalize_language,
    process_multilingual_chat,
    require_tts_supported,
)
from services.sarvam_client import synthesize_speech, transcribe_audio, translate_text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

_REDACTED = "[REDACTED]"

# Voice endpoint caps (D-06, T-09-05, T-09-06): the 30-second Saaras
# real-time REST cap is enforced locally as a 2MB in-memory byte bound
# checked before any provider call; only explicit audio types pass.
MAX_AUDIO_BYTES = 2 * 1024 * 1024
ALLOWED_AUDIO_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/ogg",
        "audio/opus",
        "audio/flac",
        "audio/webm",
        "audio/mp4",
        "audio/aac",
    }
)


def sanitize_detail(detail: str) -> str:
    """Strip configured secret values from an error detail before it leaves the server.

    Per D-17: replaces every occurrence of the OpenRouter and weather key
    values with a redaction marker. Reads settings lazily so tests can
    monkeypatch keys; skips empty values so ``str.replace`` never matches
    every position.
    """
    try:
        settings = get_settings()
        secrets = (
            settings.OPENROUTER_API_KEY,
            settings.WEATHER_API_KEY,
            settings.SARVAM_API_KEY,
        )
    except Exception:
        return detail
    safe = str(detail)
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, _REDACTED)
    return safe


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with WeatherGPT",
)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Accept a `ChatRequest`, delegate to the agent, return a `ChatResponse`."""
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=sanitize_detail(
                "Rate limit exceeded. Please retry after a short pause."
            ),
            headers={"Retry-After": str(retry_after)},
        )
    try:
        normalized = normalize_language(payload.language)
        if normalized == DEFAULT_LANGUAGE.lower():
            result = await run_in_threadpool(
                process_chat, message=payload.message, location=payload.location
            )
            language = DEFAULT_LANGUAGE
        else:
            try:
                canonical = canonical_language(payload.language)
            except ValueError:
                # D-02 honest fallback: unknown codes never reach the
                # provider and never crash — English reply naming support.
                return ChatResponse(
                    reply=(
                        f"Unsupported language '{payload.language}'. "
                        "I can reply in "
                        + " ".join([*SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE])
                        + " — replying in English."
                    ),
                    alert_level="Green",
                    language=DEFAULT_LANGUAGE,
                )
            result = await run_in_threadpool(
                process_multilingual_chat,
                message=payload.message,
                location=payload.location,
                language=canonical,
            )
            language = result.get("language", canonical)
    except ValueError as exc:
        logger.exception("Chat request failed with ValueError at %s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except RuntimeError as exc:
        # Missing API key or upstream LLM failure -> 502 for the client.
        logger.exception("Chat request failed with RuntimeError at %s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception("Chat request failed unexpectedly at %s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc

    return ChatResponse(
        reply=result["reply"],
        alert_level=result.get("alert_level", "Green"),
        language=language,
    )


def _check_voice_throttle(request: Request, client_ip: str) -> None:
    """Enforce the same per-IP sliding-window throttle as the chat route."""
    allowed, retry_after = check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=sanitize_detail(
                "Rate limit exceeded. Please retry after a short pause."
            ),
            headers={"Retry-After": str(retry_after)},
        )


@router.post(
    "/voice/transcribe",
    response_model=TranscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text (Saaras STT)",
)
async def voice_transcribe(
    request: Request,
    audio: UploadFile = File(..., description="Audio bytes to transcribe."),
    language_code: str = Form(
        default="unknown",
        description="BCP-47 code hint; 'unknown' lets the provider detect.",
    ),
) -> TranscribeResponse:
    """Accept multipart audio, return the transcript plus language code.

    The 2MB cap (HTTP 413) and the ten-type audio allowlist (HTTP 422) are
    enforced before any provider contact (T-09-05, T-09-06). Provider
    failures map to sanitized 502s; the key never leaves the server.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_voice_throttle(request, client_ip)
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=sanitize_detail(
                "Audio too large. Maximum upload size is 2MB."
            ),
        )
    content_type = (audio.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(
                "Unsupported audio type. Supported types: "
                + " ".join(sorted(ALLOWED_AUDIO_TYPES))
                + "."
            ),
        )
    try:
        transcript, detected = await run_in_threadpool(
            transcribe_audio,
            audio_bytes,
            audio.filename or "audio",
            language_code or "unknown",
        )
    except ValueError as exc:
        logger.exception(
            "Voice transcribe request failed with ValueError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except RuntimeError as exc:
        # Missing API key or upstream STT failure -> 502 for the client.
        logger.exception(
            "Voice transcribe request failed with RuntimeError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Voice transcribe request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc

    return TranscribeResponse(transcript=transcript, language_code=detected)


@router.post(
    "/voice/speak",
    status_code=status.HTTP_200_OK,
    summary="Synthesize text to audio (Bulbul TTS)",
    response_class=Response,
)
async def voice_speak(payload: SpeakRequest, request: Request) -> Response:
    """Accept text plus language, return raw audio bytes (audio/wav).

    as-IN is an honest HTTP 422 (D-02 — Bulbul has no as-IN voice, never
    silent substitution); the message is translated to as-IN via the
    sarvam-translate:v1 path when available, English otherwise. Provider
    failures map to sanitized 502s.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_voice_throttle(request, client_ip)
    if normalize_language(payload.language) == "as-in":
        try:
            detail = await run_in_threadpool(
                translate_text, TTS_UNSUPPORTED_MESSAGE, "en-IN", "as-IN"
            )
            if not detail:
                detail = TTS_UNSUPPORTED_MESSAGE
        except Exception:
            logger.exception(
                "as-IN speak fallback message translation failed at %s",
                request.url.path,
            )
            detail = TTS_UNSUPPORTED_MESSAGE
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(detail),
        )
    try:
        voice_language = require_tts_supported(payload.language)
        audio_bytes = await run_in_threadpool(
            synthesize_speech, payload.text, voice_language
        )
    except ValueError as exc:
        logger.exception(
            "Voice speak request failed with ValueError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except RuntimeError as exc:
        # Missing API key or upstream TTS failure -> 502 for the client.
        logger.exception(
            "Voice speak request failed with RuntimeError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Voice speak request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc

    return Response(content=audio_bytes, media_type="audio/wav")


def _check_alerts_throttle(request: Request, client_ip: str) -> None:
    """Enforce the same per-IP sliding-window throttle on alert routes."""
    allowed, retry_after = check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=sanitize_detail(
                "Rate limit exceeded. Please retry after a short pause."
            ),
            headers={"Retry-After": str(retry_after)},
        )


@router.post(
    "/alerts/subscribe",
    status_code=status.HTTP_200_OK,
    summary="Subscribe a device token to alert topics",
)
async def alerts_subscribe(payload: SubscribeRequest, request: Request) -> dict:
    """Register a token against topics; echo only the last 6 chars."""
    client_ip = request.client.host if request.client else "unknown"
    _check_alerts_throttle(request, client_ip)
    try:
        result = alert_watcher.subscribe(payload.token, payload.topics)
        counts = alert_watcher.registry_counts()
    except ValueError as exc:
        logger.exception(
            "Alert subscribe request failed with ValueError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Alert subscribe request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc
    return {
        "token_suffix": result["token_suffix"],
        "topics": result["topics"],
        "tokens": counts["tokens"],
        "subscribed_topics": counts["topics"],
        "subscriptions": counts["subscriptions"],
    }


@router.post(
    "/alerts/send",
    status_code=status.HTTP_200_OK,
    summary="Direct-send an Orange/Red alert",
)
async def alerts_send(payload: SendRequest, request: Request) -> dict:
    """Send one alert to exactly one target; Green/Yellow never push."""
    client_ip = request.client.host if request.client else "unknown"
    _check_alerts_throttle(request, client_ip)
    has_token = bool((payload.token or "").strip())
    has_topic = bool((payload.topic or "").strip())
    try:
        if has_token == has_topic:
            raise ValueError("Provide exactly one of token or topic.")
        level = (payload.alert_level or "").strip()
        if level not in ("Orange", "Red"):
            raise ValueError(
                "Only Orange and Red alerts may be pushed; "
                "Green and Yellow never push."
            )
        account = fcm_client.load_service_account()
        if account is None:
            raise RuntimeError(
                "FCM dispatch failure: FCM is not configured. "
                "Set FCM_SERVICE_ACCOUNT_FILE to a valid service-account "
                "JSON file."
            )
        location = (payload.location or "Mumbai").strip() or "Mumbai"
        if has_token:
            name = await run_in_threadpool(
                fcm_client.send_to_token,
                (payload.token or "").strip(),
                payload.title,
                payload.body,
                level,
                location,
            )
            target = "token"
        else:
            name = await run_in_threadpool(
                fcm_client.send_to_topic,
                (payload.topic or "").strip(),
                payload.title,
                payload.body,
                level,
                location,
            )
            target = "topic"
    except ValueError as exc:
        logger.exception(
            "Alert send request failed with ValueError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except RuntimeError as exc:
        logger.exception(
            "Alert send request failed with RuntimeError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Alert send request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc
    return {
        "message_name": name,
        "alert_level": level,
        "location": location,
        "target": target,
    }


@router.post(
    "/alerts/check",
    response_model=CheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Hourly watcher cron target",
)
async def alerts_check(request: Request) -> CheckResponse:
    """Run the 18-city watch cycle server-side (hourly cron target)."""
    client_ip = request.client.host if request.client else "unknown"
    _check_alerts_throttle(request, client_ip)
    try:
        report = await run_in_threadpool(alert_watcher.run_watch_cycle)
    except RuntimeError as exc:
        logger.exception(
            "Alert check request failed with RuntimeError at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_detail(str(exc)),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Alert check request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc
    return CheckResponse(
        checked=int(report.get("checked", 0)),
        dispatched=list(report.get("dispatched", [])),
        skipped=list(report.get("skipped", [])),
    )


@router.get(
    "/alerts/status",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Alert watcher operability snapshot",
)
async def alerts_status(request: Request) -> StatusResponse:
    """Return watch counts plus the FCM-configured flag; zero token bytes."""
    client_ip = request.client.host if request.client else "unknown"
    _check_alerts_throttle(request, client_ip)
    try:
        counts = alert_watcher.registry_counts()
        try:
            configured = fcm_client.load_service_account() is not None
        except Exception:
            logger.exception("Alert status service-account probe failed")
            configured = False
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception(
            "Alert status request failed unexpectedly at %s", request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_detail("Unexpected error: request failed."),
        ) from exc
    return StatusResponse(
        watch_cities=len(alert_watcher.WATCH_CITIES),
        cooldown_hours=int(alert_watcher.COOLDOWN_S // 3600),
        tokens=int(counts.get("tokens", 0)),
        topics=int(counts.get("topics", 0)),
        subscriptions=int(counts.get("subscriptions", 0)),
        fcm_configured=bool(configured),
    )
