"""App initialization and CORS setup."""

import logging
import re
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as chat_router
from core.config import get_cors_allow_origins, get_settings

_configured_logging = False


def _configure_logging() -> None:
    """Configure stdlib INFO logging once; reimports must not duplicate handlers."""
    global _configured_logging
    if _configured_logging or logging.getLogger().handlers:
        _configured_logging = True
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _configured_logging = True


_configure_logging()

logger = logging.getLogger("weathergpt")

# Incoming X-Request-ID is untrusted: echo only letters/digits/hyphens, <=64 chars.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "WeatherGPT backend (SIH26068) — Conversational AI for Weather "
        "Forecasting, Alerts, and Climate Information."
    ),
)

# CORS allowlist from the CORS_ALLOW_ORIGINS env var (D-06): star-open for
# local dev when unset; exact-match origin list when set, with credentials
# enabled only for the explicit list (T-07-02).
_cors_allow_origins = get_cors_allow_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins,
    allow_credentials=(_cors_allow_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Stamp every response with X-Request-ID and log one INFO line per request.

    Registered after CORSMiddleware so it executes outermost and stamps error
    responses too. Echoes an incoming id only when it matches the safe pattern;
    otherwise generates a fresh UUID4.
    """
    incoming = request.headers.get("x-request-id")
    request_id = (
        incoming if incoming and _REQUEST_ID_RE.match(incoming) else str(uuid.uuid4())
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.info(
            "%s %s 500 request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )
        raise
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        request_id,
    )
    return response


app.include_router(chat_router, prefix="/api")


@app.get("/health", tags=["system"], summary="Health check")
async def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["system"], include_in_schema=False)
async def root() -> dict:
    """Root hint for humans hitting the base URL."""
    return {"message": f"{settings.APP_NAME} API is running. See /docs.", "health": "/health"}
