"""Error-contract tests: every sad path of POST /api/chat.

The LLM is kept out of the suite: the missing-key test fails fast in
``validate_secrets`` before any network call, the outage test stubs the
executor, and the remaining tests patch ``process_chat`` in the
``api.routes`` namespace (the route uses a from-import binding, so patching
``services.agent.process_chat`` alone would have no effect on the route).
"""

import re
from unittest.mock import MagicMock, patch

import httpx
import pytest

from core.config import get_settings
from main import app
from services import agent as agent_module


def _client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _assert_no_leak(detail: str):
    """Client bodies carry safe prefixes only — no tracebacks, frames, or keys."""
    assert "Traceback" not in detail
    assert 'File "' not in detail
    # Raw exception module paths look like `pkg.mod.Class`; safe prefixes don't.
    assert not re.search(r"[a-zA-Z_][\w]*(\.[\w]+)+\.(Error|Exception|Warning)", detail)
    settings = get_settings()
    for secret in (settings.OPENROUTER_API_KEY, settings.WEATHER_API_KEY):
        if secret:
            assert secret not in detail


@pytest.mark.asyncio
async def test_missing_key_yields_502(monkeypatch):
    """No OPENROUTER_API_KEY -> 502 via the real process_chat path."""
    # Empty (not deleted): Settings also reads the repo `.env` file, so only
    # an empty env value guarantees `validate_secrets` fires without touching
    # the network.
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    get_settings.cache_clear()
    agent_module.reset_agent_cache()
    try:
        async with _client() as client:
            response = await client.post(
                "/api/chat",
                json={"message": "Will it rain in Mumbai?", "location": "Mumbai"},
            )
    finally:
        get_settings.cache_clear()
        agent_module.reset_agent_cache()
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "OPENROUTER_API_KEY" in detail
    _assert_no_leak(detail)


@pytest.mark.asyncio
async def test_llm_outage_yields_502_with_retry():
    """Forced executor failure retries once, then surfaces an honest 502 (never 200)."""
    failing_executor = MagicMock()
    failing_executor.invoke.side_effect = ConnectionError("upstream down")
    with patch.object(agent_module, "_get_executor", return_value=failing_executor):
        async with _client() as client:
            response = await client.post(
                "/api/chat",
                json={"message": "Will it rain in Mumbai?", "location": "Mumbai"},
            )
    assert response.status_code == 502
    assert response.status_code != 200
    # Initial call plus exactly one retry.
    assert failing_executor.invoke.call_count == agent_module.LLM_MAX_ATTEMPTS == 2
    detail = response.json()["detail"]
    assert "WeatherGPT agent invocation failed" in detail
    _assert_no_leak(detail)


@pytest.mark.asyncio
async def test_unexpected_failure_yields_generic_500():
    """A generic exception behind the route becomes a fixed-prefix 500."""
    with patch(
        "api.routes.process_chat", side_effect=KeyError("some-internal-state")
    ):
        async with _client() as client:
            response = await client.post(
                "/api/chat",
                json={"message": "Will it rain in Mumbai?", "location": "Mumbai"},
            )
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail.startswith("Unexpected error")
    assert "some-internal-state" not in detail
    _assert_no_leak(detail)


@pytest.mark.asyncio
async def test_schema_limits_yield_422():
    """Empty / overlong messages and overlong locations are rejected with 422."""
    async with _client() as client:
        empty = await client.post("/api/chat", json={"message": ""})
        too_long = await client.post(
            "/api/chat", json={"message": "x" * 2001, "location": "Mumbai"}
        )
        bad_location = await client.post(
            "/api/chat",
            json={"message": "Will it rain?", "location": "y" * 121},
        )
    for response in (empty, too_long, bad_location):
        assert response.status_code == 422
        _assert_no_leak(str(response.json()))


@pytest.mark.asyncio
async def test_whitespace_padded_valid_message_accepted():
    """A padded-but-valid message within limits still returns 200."""
    fake_result = {"reply": "Clear skies over Mumbai.\nAlert: Green", "alert_level": "Green"}
    async with _client() as client:
        with patch("api.routes.process_chat", return_value=fake_result):
            response = await client.post(
                "/api/chat",
                json={"message": "   Will it rain in Mumbai?   ", "location": "Mumbai"},
            )
    assert response.status_code == 200
    assert response.json()["alert_level"] == "Green"


def test_sanitize_helper_redacts_configured_keys(monkeypatch):
    """Sanitize helper replaces both key values with the redaction marker (D-17)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-sentinel-123")
    monkeypatch.setenv("WEATHER_API_KEY", "wx-sentinel-456")
    get_settings.cache_clear()
    try:
        from api.routes import sanitize_detail

        dirty = "failed with sk-or-sentinel-123 and wx-sentinel-456 inside"
        clean = sanitize_detail(dirty)
        assert "sk-or-sentinel-123" not in clean
        assert "wx-sentinel-456" not in clean
        assert "[REDACTED]" in clean
    finally:
        get_settings.cache_clear()
