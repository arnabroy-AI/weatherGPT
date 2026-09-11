"""Demo-hardening tracer tests: CORS allowlist + per-IP throttle (D-06).

The LLM is kept out of the suite by patching ``process_chat`` inside the
``api.routes`` namespace (the route uses a from-import binding, so patching
``services.agent.process_chat`` alone would have no effect on the route).
Throttle buckets are reset by the autouse conftest fixture, so each test
starts with a fresh sliding window.
"""

from unittest.mock import patch

import httpx
import pytest

from core.config import get_settings
from main import app

_FAKE_RESULT = {
    "reply": "Clear skies over Mumbai, 29.5 C.\nAlert: Green",
    "alert_level": "Green",
}

_CHAT_BODY = {"message": "Weather in Mumbai?", "location": "Mumbai"}

_DUMMY_KEY = "test-dummy-key"


def _client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_chat_single_post_still_succeeds():
    """Happy path: one POST /api/chat returns 200 (mocked agent)."""
    async with _client() as client:
        with patch("api.routes.process_chat", return_value=_FAKE_RESULT):
            response = await client.post("/api/chat", json=_CHAT_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == _FAKE_RESULT["reply"]
    assert body["alert_level"] == "Green"


@pytest.mark.asyncio
async def test_chat_throttle_returns_429_with_retry_after(monkeypatch):
    """Over-limit POSTs return 429 JSON plus a Retry-After header."""
    monkeypatch.setenv("CHAT_THROTTLE_PER_MIN", "2")
    get_settings.cache_clear()
    try:
        async with _client() as client:
            with patch("api.routes.process_chat", return_value=_FAKE_RESULT):
                first = await client.post("/api/chat", json=_CHAT_BODY)
                second = await client.post("/api/chat", json=_CHAT_BODY)
                throttled = await client.post("/api/chat", json=_CHAT_BODY)
    finally:
        get_settings.cache_clear()
    assert first.status_code == 200
    assert second.status_code == 200
    assert throttled.status_code == 429
    assert "Retry-After" in throttled.headers
    assert int(throttled.headers["Retry-After"]) >= 1
    assert "detail" in throttled.json()


@pytest.mark.asyncio
async def test_cors_star_open_when_allowlist_unset():
    """Default (no CORS_ALLOW_ORIGINS): any Origin gets a wildcard ACAO."""
    get_settings.cache_clear()
    async with _client() as client:
        response = await client.get(
            "/health", headers={"Origin": "http://localhost:3000"}
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


@pytest.mark.asyncio
async def test_cors_reflects_explicit_origin_allowlist(monkeypatch):
    """Set allowlist: listed Origin echoed, unlisted Origin gets no ACAO."""
    import importlib

    import main as main_module

    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://demo.example, https://sih.example")
    get_settings.cache_clear()
    importlib.reload(main_module)
    try:
        transport = httpx.ASGITransport(app=main_module.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            allowed = await client.get(
                "/health", headers={"Origin": "https://demo.example"}
            )
            denied = await client.get(
                "/health", headers={"Origin": "https://evil.example"}
            )
    finally:
        get_settings.cache_clear()
        importlib.reload(main_module)
    assert allowed.headers.get("access-control-allow-origin") == "https://demo.example"
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.asyncio
async def test_throttle_and_cors_bodies_carry_no_key_material(monkeypatch):
    """429 bodies and CORS responses never contain the dummy key value."""
    monkeypatch.setenv("CHAT_THROTTLE_PER_MIN", "1")
    get_settings.cache_clear()
    try:
        async with _client() as client:
            with patch("api.routes.process_chat", return_value=_FAKE_RESULT):
                ok_response = await client.post("/api/chat", json=_CHAT_BODY)
                throttled = await client.post(
                    "/api/chat",
                    json=_CHAT_BODY,
                    headers={"Origin": "http://localhost:3000"},
                )
    finally:
        get_settings.cache_clear()
    assert ok_response.status_code == 200
    assert throttled.status_code == 429
    assert _DUMMY_KEY not in throttled.text
    assert _DUMMY_KEY not in ok_response.text
