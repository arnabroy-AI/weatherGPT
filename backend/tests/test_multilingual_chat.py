"""Hindi round-trip tracer tests (Phase 9, Plan 01).

Sarvam HTTP is mocked via httpx.MockTransport injected at the
``services.sarvam_client`` transport seam; the LLM is kept out of the suite
by patching ``services.agent._get_executor`` with a FakeExecutor returning a
canned English reply. No test performs live network access.
"""

import json
from unittest.mock import patch

import httpx
import pytest

from main import app
from services import agent as agent_module
from services import sarvam_client
from services.multilingual import process_multilingual_chat
from services.sarvam_client import translate_text

CANNED_ENGLISH_REPLY = (
    "Current weather in Mumbai: 29.5 C, Partly cloudy "
    "(non-IMD model data; source: open-meteo-live). Stay hydrated.\n"
    "Alert: Green"
)

HINDI_QUERY = "\u092e\u0941\u0902\u092c\u0908 \u092e\u0947\u0902 \u092e\u094c\u0938\u092e \u0915\u0948\u0938\u093e \u0939\u0948?"


class FakeExecutor:
    """Mocked-LLM seam: canned reply, no intermediate tool steps."""

    def __init__(self, output: str):
        self._output = output

    def invoke(self, _payload):
        return {"output": self._output, "intermediate_steps": []}


def _translate_transport(calls: list) -> httpx.MockTransport:
    """Mock Sarvam translate: hi-IN->en-IN returns an English query,
    en-IN->hi-IN returns a Hindi reply preserving 29.5 byte-identical."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        calls.append(body)
        assert request.url.path == "/translate"
        assert request.headers["api-subscription-key"] == "test-sarvam-key"
        assert body["model"] == "mayura:v1"
        assert body["numerals_format"] == "international"
        source = body["source_language_code"]
        if source == "hi-IN":
            return httpx.Response(
                200, json={"translated_text": "What is the weather in Mumbai?"}
            )
        return httpx.Response(
            200,
            json={
                "translated_text": (
                    "\u092e\u0941\u0902\u092c\u0908 \u092e\u0947\u0902 \u092e\u094c\u0938\u092e: "
                    "29.5 C, \u0906\u0902\u0936\u093f\u0915 \u092c\u093e\u0926\u0932\u0964\n"
                    "Alert: Green"
                )
            },
        )

    return httpx.MockTransport(handler)


@pytest.fixture
def sarvam_key(monkeypatch):
    """Pin a sentinel Sarvam key so no test depends on the real .env value."""
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    sarvam_client.get_settings.cache_clear() if hasattr(
        sarvam_client.get_settings, "cache_clear"
    ) else None
    from core.config import get_settings

    get_settings.cache_clear()
    try:
        yield "test-sarvam-key"
    finally:
        get_settings.cache_clear()
        sarvam_client.reset_transport()


def test_translate_client_posts_expected_shape(sarvam_key):
    """Translate POST carries the Mayura body keys plus the key header."""
    calls: list = []
    transport = _translate_transport(calls)
    out = translate_text(HINDI_QUERY, "hi-IN", "en-IN", transport=transport)
    assert out == "What is the weather in Mumbai?"
    assert len(calls) == 1
    body = calls[0]
    assert body["input"] == HINDI_QUERY
    assert body["source_language_code"] == "hi-IN"
    assert body["target_language_code"] == "en-IN"


def test_translate_missing_key_raises_sanitized(monkeypatch):
    """Missing SARVAM_API_KEY raises without leaking anything secret-like."""
    monkeypatch.setenv("SARVAM_API_KEY", "")
    from core.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="Sarvam translate failure"):
            translate_text("hello", "en-IN", "hi-IN")
    finally:
        get_settings.cache_clear()


def test_translate_non_200_raises_sanitized(sarvam_key):
    """Upstream 500 becomes a sanitized RuntimeError mentioning the status."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with pytest.raises(RuntimeError, match="status 500"):
        translate_text("hello", "en-IN", "hi-IN", transport=httpx.MockTransport(handler))


def test_translate_chunks_overlong_input(sarvam_key):
    """Inputs over 1000 chars split into ordered sub-1000-char requests."""
    calls: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        calls.append(body)
        assert len(body["input"]) <= 1000
        return httpx.Response(200, json={"translated_text": f"chunk-{len(calls)}"})

    long_text = " ".join(f"Sentence number {i} about Mumbai weather." for i in range(60))
    assert len(long_text) > 1000
    out = translate_text(long_text, "en-IN", "hi-IN", transport=httpx.MockTransport(handler))
    assert len(calls) > 1
    assert out == " ".join(f"chunk-{i}" for i in range(1, len(calls) + 1))


def test_hindi_round_trip_preserves_digits(sarvam_key):
    """Devanagari query -> mocked Sarvam -> mocked agent -> Hindi reply.

    The Hindi reply keeps 29.5 byte-identical and alert_level is Green.
    """
    calls: list = []
    sarvam_client.set_transport(_translate_transport(calls))
    fake = FakeExecutor(CANNED_ENGLISH_REPLY)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_multilingual_chat(HINDI_QUERY, location="Mumbai", language="hi-IN")
    assert "29.5" in result["reply"]
    assert result["alert_level"] == "Green"
    assert result["language"] == "hi-IN"
    # Exactly two translate calls: hi->en query, en->hi reply.
    assert [c["source_language_code"] for c in calls] == ["hi-IN", "en-IN"]
    assert calls[1]["input"] == CANNED_ENGLISH_REPLY


def test_multilingual_english_passthrough_uses_frozen_core(sarvam_key):
    """en-IN (or absent language) delegates straight to process_chat."""
    fake = FakeExecutor(CANNED_ENGLISH_REPLY)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_multilingual_chat("Weather in Mumbai?", location="Mumbai")
    assert result["reply"] == CANNED_ENGLISH_REPLY
    assert result["alert_level"] == "Green"
    assert result["language"] == "en-IN"


def _route_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_route_hindi_round_trip_preserves_digits(sarvam_key):
    """POST Devanagari + hi-IN flows route -> orchestration -> mocked
    Sarvam + mocked agent; Hindi reply keeps 29.5 byte-identical."""
    calls: list = []
    sarvam_client.set_transport(_translate_transport(calls))
    fake = FakeExecutor(CANNED_ENGLISH_REPLY)
    async with _route_client() as client:
        with patch.object(agent_module, "_get_executor", return_value=fake):
            response = await client.post(
                "/api/chat",
                json={"message": HINDI_QUERY, "location": "Mumbai", "language": "hi-IN"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "hi-IN"
    assert body["alert_level"] == "Green"
    assert "29.5" in body["reply"]


async def test_route_without_language_defaults_to_english():
    """No language field keeps the exact existing English path untouched."""
    fake_result = {"reply": CANNED_ENGLISH_REPLY, "alert_level": "Green"}
    async with _route_client() as client:
        with patch("api.routes.process_chat", return_value=fake_result):
            response = await client.post(
                "/api/chat",
                json={"message": "Weather in Mumbai?", "location": "Mumbai"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en-IN"
    assert body["reply"] == CANNED_ENGLISH_REPLY


async def test_route_unsupported_language_replies_honest_english():
    """Unknown xx-YY never crashes: HTTP 200 English reply naming hi-IN."""
    async with _route_client() as client:
        response = await client.post(
            "/api/chat",
            json={"message": HINDI_QUERY, "location": "Mumbai", "language": "xx-YY"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en-IN"
    assert "hi-IN" in body["reply"]
