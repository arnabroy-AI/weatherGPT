"""Sarvam secret-safety tests: key material never leaks into logs or responses (D-06).

Mirrors tests/test_secrets.py: all three key env vars point at unique
sentinel markers, caches are cleared, a Sarvam outage plus an LLM outage are
forced through the real multilingual chat and transcribe paths (direct calls
and HTTP route bodies), then no sentinel may appear in the raised errors, the
response bodies, or captured log output. A sanitize_detail unit check pins
Sarvam redaction for every route including both voice endpoints.
"""

import json
import logging

import httpx
import pytest

from api.routes import sanitize_detail
from main import app
from services import agent as agent_module
from services import sarvam_client

SENTINEL_OPENROUTER = "sk-or-SENTINEL-9f8e7d6c5b4a-UNIQUE"
SENTINEL_WEATHER = "wx-SENTINEL-1a2b3c4d5e6f-UNIQUE"
SENTINEL_SARVAM = "sv-SENTINEL-7c3d9a1b2e4f-UNIQUE"

HINDI_QUERY = "\u092e\u0941\u092c\u0908 \u092e\u0947\u0902 \u092e\u094c\u0938\u092e \u0915\u0948\u0938\u093e \u0939\u0948?"


def _point_keys_at_sentinels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point all three keys at sentinels and clear cached singletons."""
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL_OPENROUTER)
    monkeypatch.setenv("WEATHER_API_KEY", SENTINEL_WEATHER)
    monkeypatch.setenv("SARVAM_API_KEY", SENTINEL_SARVAM)
    from core.config import get_settings

    get_settings.cache_clear()
    agent_module.reset_agent_cache()
    sarvam_client.reset_transport()


def _assert_no_sentinels(*texts: str) -> None:
    for text in texts:
        assert SENTINEL_OPENROUTER not in text
        assert SENTINEL_WEATHER not in text
        assert SENTINEL_SARVAM not in text


def _sarvam_outage_transport(calls: list) -> httpx.MockTransport:
    """Fail every Sarvam surface with a non-200 (simulated provider outage)."""

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(500, json={"error": "simulated sarvam outage"})

    return httpx.MockTransport(handler)


def _sarvam_echo_transport() -> httpx.MockTransport:
    """Succeed translate calls (tagged echo, digits intact) for the LLM-outage test."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["api-subscription-key"] == SENTINEL_SARVAM
        if request.url.path == "/translate":
            body = json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                200,
                json={
                    "translated_text": f"[{body['target_language_code']}] {body['input']}"
                },
            )
        return httpx.Response(404, json={"error": "unexpected path"})

    return httpx.MockTransport(handler)


def test_multilingual_chat_outage_leaks_no_keys(monkeypatch, caplog):
    """Forced translate outage through the real multilingual path stays clean."""
    _point_keys_at_sentinels(monkeypatch)
    calls: list = []
    sarvam_client.set_transport(_sarvam_outage_transport(calls))
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError) as exc_info:
                sarvam_client.translate_text(HINDI_QUERY, "hi-IN", "en-IN")
    finally:
        sarvam_client.reset_transport()
    assert calls == ["/translate"]
    _assert_no_sentinels(str(exc_info.value), caplog.text)


@pytest.mark.asyncio
async def test_chat_route_multilingual_failure_leaks_no_keys(monkeypatch, caplog):
    """502 multilingual chat body and request logs carry no key material."""
    _point_keys_at_sentinels(monkeypatch)
    calls: list = []
    sarvam_client.set_transport(_sarvam_outage_transport(calls))
    try:
        transport = httpx.ASGITransport(app=app)
        with caplog.at_level(logging.INFO):
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/chat",
                    json={
                        "message": HINDI_QUERY,
                        "location": "Mumbai",
                        "language": "hi-IN",
                    },
                )
    finally:
        sarvam_client.reset_transport()
    assert response.status_code == 502
    assert calls == ["/translate"]
    _assert_no_sentinels(response.text, caplog.text)


def test_transcribe_outage_leaks_no_keys(monkeypatch, caplog):
    """Forced STT outage through the real transcribe path stays clean."""
    _point_keys_at_sentinels(monkeypatch)
    calls: list = []
    sarvam_client.set_transport(_sarvam_outage_transport(calls))
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError) as exc_info:
                sarvam_client.transcribe_audio(
                    b"RIFF\x24\x00\x00\x00WAVEfmt fake-upload", "t.wav", "hi-IN"
                )
    finally:
        sarvam_client.reset_transport()
    assert calls == ["/speech-to-text"]
    _assert_no_sentinels(str(exc_info.value), caplog.text)


@pytest.mark.asyncio
async def test_transcribe_route_failure_leaks_no_keys(monkeypatch, caplog):
    """502 transcribe body and request logs carry no key material."""
    _point_keys_at_sentinels(monkeypatch)
    calls: list = []
    sarvam_client.set_transport(_sarvam_outage_transport(calls))
    try:
        transport = httpx.ASGITransport(app=app)
        with caplog.at_level(logging.INFO):
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/voice/transcribe",
                    files={"audio": ("t.wav", b"RIFFfake", "audio/wav")},
                    data={"language_code": "hi-IN"},
                )
    finally:
        sarvam_client.reset_transport()
    assert response.status_code == 502
    _assert_no_sentinels(response.text, caplog.text)


def test_llm_outage_with_sarvam_key_leaks_no_keys(monkeypatch, caplog):
    """LLM outage mid-round-trip keeps the Sarvam sentinel out of errors/logs."""
    _point_keys_at_sentinels(monkeypatch)
    sarvam_client.set_transport(_sarvam_echo_transport())

    def _boom(self, *args, **kwargs):
        raise ConnectionError("simulated provider outage")

    monkeypatch.setattr("langchain_classic.agents.AgentExecutor.invoke", _boom)
    try:
        from services.multilingual import process_multilingual_chat

        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError) as exc_info:
                process_multilingual_chat(
                    HINDI_QUERY, location="Mumbai", language="hi-IN"
                )
    finally:
        sarvam_client.reset_transport()
    _assert_no_sentinels(str(exc_info.value), caplog.text)


def test_sanitize_detail_redacts_sarvam_sentinel(monkeypatch):
    """sanitize_detail replaces the Sarvam sentinel with the redaction marker."""
    _point_keys_at_sentinels(monkeypatch)
    redacted = sanitize_detail(f"upstream boom carrying {SENTINEL_SARVAM} inline")
    assert SENTINEL_SARVAM not in redacted
    assert "[REDACTED]" in redacted
    # Sibling keys stay redacted on the same path (every route shares this).
    for sentinel in (SENTINEL_OPENROUTER, SENTINEL_WEATHER):
        assert sentinel not in sanitize_detail(f"failure {sentinel} here")
