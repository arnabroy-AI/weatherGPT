"""FCM v1 thin client with an injectable auth seam (Phase 10, D-02 tracer).

Sends Orange/Red alert payloads through Google FCM v1 over raw ``httpx``
(token path plus topic path) with zero new runtime dependencies.

Auth design (planner decision: seam option b, not ``google-auth``):
- Tests and CI inject a fake bearer via :func:`set_token_provider` — no
  crypto, no network, no key material anywhere near the test process.
- Live sends lazily import ``google.oauth2.service_account`` inside
  :func:`get_access_token`. ``google-auth`` is an intentional opt-in
  (``pip install google-auth``); it is never imported at module scope and
  never added to ``backend/requirements.txt`` (T-10-SC).

Security posture (T-10-01, T-10-02, T-10-03):
- The private key, access token, and service-account JSON are only ever
  placed on the outbound ``Authorization: Bearer`` header / Google OAuth
  call. They are never logged, never printed, and never embedded in an
  exception message. Failures are logged server-side via
  ``logger.exception`` (status code only) and surfaced as sanitized
  ``RuntimeError`` values the routes map to 502/503.
- A missing service-account file disables cleanly: :func:`load_service_account`
  returns ``None`` and the send paths raise a ``RuntimeError`` carrying the
  words "not configured". Nothing crashes at import.
- Token and topic values are length/shape validated before send; empty
  values raise ``ValueError``.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10.0

FCM_SEND_URL_TEMPLATE = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

# OAuth scope minted for live FCM v1 sends (opt-in google-auth path only).
FCM_OAUTH_SCOPES = ("https://www.googleapis.com/auth/firebase.messaging",)

# Service-account JSON fields every send path requires (T-10-02: the loader
# validates shape and never echoes contents).
_REQUIRED_SA_FIELDS = ("type", "project_id", "private_key", "client_email", "token_uri")

# T-10-03: pre-send shape bounds. FCM registration tokens are long opaque
# strings; topic names must match the FCM topic charset.
_MAX_TOKEN_CHARS = 4096
_MAX_TOPIC_CHARS = 900
_TOPIC_RE = re.compile(r"[a-zA-Z0-9\-_.~%]+")
_MAX_TITLE_CHARS = 200
_MAX_BODY_CHARS = 1000

# Module-level transport override for tests (httpx.MockTransport), mirroring
# the services/sarvam_client.py set_transport pattern. Production leaves None.
_TRANSPORT_OVERRIDE: Optional[httpx.BaseTransport] = None

# Module-level bearer seam for tests (option b): a zero-arg callable
# returning a fake access token. Production leaves None so the lazy
# google-auth path inside get_access_token is used.
_TOKEN_PROVIDER_OVERRIDE: Optional[Callable[..., str]] = None


def set_transport(transport: Optional[httpx.BaseTransport]) -> None:
    """Pin a transport (e.g. httpx.MockTransport) for tests; None restores live."""
    global _TRANSPORT_OVERRIDE
    _TRANSPORT_OVERRIDE = transport


def reset_transport() -> None:
    """Clear any test transport override."""
    set_transport(None)


def set_token_provider(provider: Optional[Callable[..., str]]) -> None:
    """Pin a bearer provider for tests; None restores the live google-auth path."""
    global _TOKEN_PROVIDER_OVERRIDE
    _TOKEN_PROVIDER_OVERRIDE = provider


def reset_token_provider() -> None:
    """Clear any test token-provider override."""
    set_token_provider(None)


def _active_transport(transport: Optional[httpx.BaseTransport]) -> Optional[httpx.BaseTransport]:
    """Per-call override wins; otherwise fall back to the module override."""
    return transport if transport is not None else _TRANSPORT_OVERRIDE


def load_service_account(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load and shape-validate the FCM service-account JSON.

    Args:
        path: Optional explicit file path. Defaults to the
            ``FCM_SERVICE_ACCOUNT_FILE`` setting. Never crashes at import;
            resolution happens per call so tests can repoint the setting.

    Returns:
        The parsed service-account dict, or ``None`` when the file is
        absent (missing file disables cleanly per the carryover).

    Raises:
        RuntimeError: Sanitized failure for malformed JSON or a dict
            missing any required field. Never echoes file contents.
    """
    resolved = path if path is not None else get_settings().FCM_SERVICE_ACCOUNT_FILE
    candidate = Path(resolved)
    if not candidate.is_file():
        return None
    try:
        raw = candidate.read_text(encoding="utf-8")
    except OSError as exc:
        logger.exception("FCM service-account file unreadable")
        raise RuntimeError("FCM dispatch failure: service-account file unreadable.") from exc
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        logger.exception("FCM service-account file holds malformed JSON")
        raise RuntimeError("FCM dispatch failure: malformed service-account file.") from exc
    if not isinstance(data, dict) or any(
        not isinstance(data.get(field), str) or not data.get(field)
        for field in _REQUIRED_SA_FIELDS
    ):
        logger.exception("FCM service-account file missing required fields")
        raise RuntimeError(
            "FCM dispatch failure: service-account file is missing required fields."
        )
    return data


def get_access_token(service_account: Optional[Dict[str, Any]] = None) -> str:
    """Mint (or inject) the OAuth bearer for FCM v1.

    The injected test provider wins when set via :func:`set_token_provider`
    (called with no args; a provider accepting the service-account dict is
    also tolerated). Otherwise this lazily imports
    ``google.oauth2.service_account`` — absent in this repo by design
    (T-10-SC) — and raises a clear opt-in error naming the install.

    Args:
        service_account: Optional parsed service-account dict; loaded via
            :func:`load_service_account` when omitted.

    Raises:
        RuntimeError: Sanitized failure (FCM not configured, google-auth
            opt-in missing, or mint failure). Never carries key material.
    """
    if _TOKEN_PROVIDER_OVERRIDE is not None:
        try:
            try:
                return _TOKEN_PROVIDER_OVERRIDE()
            except TypeError:
                return _TOKEN_PROVIDER_OVERRIDE(service_account)
        except Exception as exc:
            logger.exception("FCM token provider failed")
            raise RuntimeError("FCM dispatch failure: token provider failed.") from exc
    try:
        from google.oauth2 import service_account as sa_module
        from google.auth.transport.requests import Request as AuthRequest
    except ImportError as exc:
        raise RuntimeError(
            "FCM dispatch failure: google-auth is not installed. "
            "Install it with `pip install google-auth` to enable live FCM sends."
        ) from exc
    account = service_account if service_account is not None else load_service_account()
    if account is None:
        raise RuntimeError(
            "FCM dispatch failure: FCM is not configured. "
            "Set FCM_SERVICE_ACCOUNT_FILE to a valid service-account JSON file."
        )
    try:
        credentials = sa_module.Credentials.from_service_account_info(
            account, scopes=list(FCM_OAUTH_SCOPES)
        )
        credentials.refresh(AuthRequest())
        token = credentials.token
    except Exception as exc:
        logger.exception("FCM access-token mint failed")
        raise RuntimeError("FCM dispatch failure: access-token mint failed.") from exc
    if not token or not isinstance(token, str):
        raise RuntimeError("FCM dispatch failure: access-token mint failed.")
    return token


def _require_token_shape(token: str) -> str:
    """Validate a device registration token; return it stripped."""
    cleaned = (token or "").strip()
    if not cleaned:
        raise ValueError("token must be a non-empty string.")
    if len(cleaned) > _MAX_TOKEN_CHARS:
        raise ValueError("token exceeds the maximum length.")
    return cleaned


def _require_topic_shape(topic: str) -> str:
    """Validate an FCM topic name (no /topics/ prefix); return it stripped."""
    cleaned = (topic or "").strip()
    if not cleaned:
        raise ValueError("topic must be a non-empty string.")
    if cleaned.startswith("/topics/"):
        cleaned = cleaned[len("/topics/"):]
    if not cleaned or len(cleaned) > _MAX_TOPIC_CHARS or _TOPIC_RE.fullmatch(cleaned) is None:
        raise ValueError("topic must match the FCM topic charset [a-zA-Z0-9-_.~%].")
    return cleaned


def _send_message(
    message: Dict[str, Any],
    alert_level: str,
    target_kind: str,
    transport: Optional[httpx.BaseTransport],
) -> str:
    """POST one FCM v1 message dict; return the response ``name`` field."""
    account = load_service_account()
    if account is None:
        raise RuntimeError(
            "FCM dispatch failure: FCM is not configured. "
            "Set FCM_SERVICE_ACCOUNT_FILE to a valid service-account JSON file."
        )
    project_id = account["project_id"]
    url = FCM_SEND_URL_TEMPLATE.format(project_id=project_id)
    access_token = get_access_token(account)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"message": message}
    try:
        with httpx.Client(
            transport=_active_transport(transport), timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = client.post(url, json=payload, headers=headers)
    except Exception as exc:
        logger.exception("FCM send request failed")
        raise RuntimeError("FCM dispatch failure: upstream request failed.") from exc
    if response.status_code != 200:
        logger.exception("FCM send returned non-200 status=%s", response.status_code)
        raise RuntimeError(
            "FCM dispatch failure: upstream returned status "
            f"{response.status_code}."
        )
    try:
        body = response.json()
    except Exception as exc:
        logger.exception("FCM send returned unparseable JSON")
        raise RuntimeError("FCM dispatch failure: malformed upstream response.") from exc
    name = body.get("name") if isinstance(body, dict) else None
    if not name or not isinstance(name, str):
        logger.exception("FCM send response missing message name")
        raise RuntimeError("FCM dispatch failure: malformed upstream response.")
    # Key-free success line: message name plus target kind plus alert level.
    logger.info("FCM dispatch succeeded name=%s target=%s alert_level=%s", name, target_kind, alert_level)
    return name


def send_to_token(
    token: str,
    title: str,
    body: str,
    alert_level: str = "Orange",
    location: str = "Mumbai",
    transport: Optional[httpx.BaseTransport] = None,
) -> str:
    """Send an alert notification to one device token via FCM v1.

    Args:
        token: Device registration token (validated before send).
        title: Notification title (coerced to text, length-capped).
        body: Notification body (coerced to text, length-capped).
        alert_level: Severity label echoed in ``data`` (e.g. Orange/Red).
        location: Human location label echoed in ``data``.
        transport: Optional per-call transport override for tests; falls
            back to the module-level override set via :func:`set_transport`.

    Returns:
        The FCM message ``name`` (``projects/<id>/messages/<mid>``).

    Raises:
        ValueError: If ``token`` is empty or overlong.
        RuntimeError: Sanitized dispatch failure (not configured, non-200
            carrying only the status code, malformed response). Never
            carries token or key bytes.
    """
    cleaned_token = _require_token_shape(token)
    safe_level = str(alert_level or "")[:20] or "Orange"
    safe_location = str(location or "")[:80] or "Unknown"
    message = {
        "token": cleaned_token,
        "notification": {
            "title": str(title or "")[:_MAX_TITLE_CHARS],
            "body": str(body or "")[:_MAX_BODY_CHARS],
        },
        "data": {"alert_level": safe_level, "location": safe_location},
    }
    return _send_message(message, safe_level, "token", transport)


def send_to_topic(
    topic: str,
    title: str,
    body: str,
    alert_level: str = "Orange",
    location: str = "Mumbai",
    transport: Optional[httpx.BaseTransport] = None,
) -> str:
    """Send an alert notification to an FCM topic via FCM v1.

    Args:
        topic: Topic name without the ``/topics/`` prefix (validated
            before send; a prefixed value is tolerated and stripped).
        title: Notification title (coerced to text, length-capped).
        body: Notification body (coerced to text, length-capped).
        alert_level: Severity label echoed in ``data`` (e.g. Orange/Red).
        location: Human location label echoed in ``data``.
        transport: Optional per-call transport override for tests; falls
            back to the module-level override set via :func:`set_transport`.

    Returns:
        The FCM message ``name`` (``projects/<id>/messages/<mid>``).

    Raises:
        ValueError: If ``topic`` is empty, overlong, or outside the FCM
            topic charset.
        RuntimeError: Sanitized dispatch failure (not configured, non-200
            carrying only the status code, malformed response). Never
            carries topic or key bytes.
    """
    cleaned_topic = _require_topic_shape(topic)
    safe_level = str(alert_level or "")[:20] or "Orange"
    safe_location = str(location or "")[:80] or "Unknown"
    message = {
        "topic": cleaned_topic,
        "notification": {
            "title": str(title or "")[:_MAX_TITLE_CHARS],
            "body": str(body or "")[:_MAX_BODY_CHARS],
        },
        "data": {"alert_level": safe_level, "location": safe_location},
    }
    return _send_message(message, safe_level, "topic", transport)
