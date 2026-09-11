"""API endpoints (traffic directors — no business logic here)."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from core.config import get_settings
from api.throttle import check_rate_limit
from schemas.chat import ChatRequest, ChatResponse
from services.agent import process_chat
from services.multilingual import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    canonical_language,
    normalize_language,
    process_multilingual_chat,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

_REDACTED = "[REDACTED]"


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
