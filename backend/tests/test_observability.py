"""Observability tests: X-Request-ID echo/generation, liveness shape, CORS (D-09/10/12).

Mirrors the httpx ASGI-client pattern from tests/test_chat_api.py.
"""

import re
import uuid
from unittest.mock import patch

import httpx
import pytest

from main import app

UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _assert_uuid4(value: str) -> None:
    assert UUID4_RE.match(value), f"not a UUID4: {value!r}"
    uuid.UUID(value, version=4)  # raises if unparseable


@pytest.mark.asyncio
async def test_request_id_echoed_on_chat():
    """A valid incoming id is echoed verbatim on the chat response."""
    fake_result = {"reply": "Sunny.", "alert_level": "Green"}
    async with _client() as client:
        with patch("api.routes.process_chat", return_value=fake_result):
            response = await client.post(
                "/api/chat",
                json={"message": "Hi", "location": "Mumbai"},
                headers={"X-Request-ID": "trace-abc-123"},
            )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-abc-123"


@pytest.mark.asyncio
async def test_request_id_echoed_on_health():
    """A valid incoming id is echoed verbatim on the health response."""
    async with _client() as client:
        response = await client.get(
            "/health", headers={"X-Request-ID": "health-trace-1"}
        )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "health-trace-1"


@pytest.mark.asyncio
async def test_request_id_generated_when_absent():
    """Missing header yields a fresh UUID4-shaped id on health and chat."""
    fake_result = {"reply": "Sunny.", "alert_level": "Green"}
    async with _client() as client:
        health = await client.get("/health")
        with patch("api.routes.process_chat", return_value=fake_result):
            chat = await client.post(
                "/api/chat", json={"message": "Hi", "location": "Mumbai"}
            )
    _assert_uuid4(health.headers["X-Request-ID"])
    _assert_uuid4(chat.headers["X-Request-ID"])


@pytest.mark.asyncio
async def test_request_id_replaced_when_unsafe():
    """Untrusted values (spaces, overlong, symbols) are replaced with UUID4."""
    bad_ids = [
        "has space",
        "x" * 65,  # over the 64-char limit
        "evil<script>",
        "semi;colon",
    ]
    async with _client() as client:
        for bad in bad_ids:
            response = await client.get("/health", headers={"X-Request-ID": bad})
            stamped = response.headers["X-Request-ID"]
            assert stamped != bad
            _assert_uuid4(stamped)


@pytest.mark.asyncio
async def test_health_body_is_liveness_only():
    """Health body key set is exactly the three liveness keys (D-10)."""
    async with _client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert set(response.json().keys()) == {"status", "app", "version"}
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_cors_allows_frontend_origin():
    """An Origin-bearing request is allowed permissively (D-12, local dev).

    Note: with allow_origins=["*"] plus allow_credentials=True, Starlette
    echoes the requesting origin instead of a literal "*" (per the fetch
    spec, "*" is forbidden with credentials). Either form proves the
    frontend origin is allowed, so accept both.
    """
    origin = "http://localhost:3000"
    async with _client() as client:
        response = await client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in ("*", origin)
