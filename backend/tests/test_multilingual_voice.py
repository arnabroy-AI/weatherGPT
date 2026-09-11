"""Six-language rows plus voice round-trips plus cap tests (Phase 9, Plan 02).

All Sarvam HTTP is mocked via httpx.MockTransport injected at the
``services.sarvam_client`` transport seam; the LLM stays out of the suite
via a FakeExecutor returning a canned English reply. No test performs live
network access.
"""

import base64
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

FAKE_WAV_BYTES = b"RIFF$\x00\x00\x00WAVEfmt fake-audio-payload-29.5"
FAKE_WAV_B64 = base64.b64encode(FAKE_WAV_BYTES).decode("ascii")

# Plan 01 covered hi-IN; this plan proves the remaining five rows.
LANGUAGE_ROWS = ["mr-IN", "ta-IN", "te-IN", "bn-IN", "as-IN"]

QUERIES = {
    "mr-IN": "\u092e\u0941\u092c\u0908\u0924\u0940\u0932 \u0939\u0935\u093e\u092e\u093e\u0928 \u0915\u0938\u0947 \u0906\u0939\u0947?",
    "ta-IN": "\u0bae\u0bc1\u0bae\u0bcd\u0baa\u0bc8\u0baf\u0bbf\u0bb2\u0bcd \u0bb5\u0bbe\u0ba9\u0bbf\u0bb2\u0bc8 \u0b8e\u0baa\u0bcd\u0baa\u0b9f\u0bbf \u0b89\u0bb3\u0bcd\u0bb3\u0ba4\u0bc1?",
    "te-IN": "\u0c2e\u0c41\u0c02\u0c2c\u0c48\u0c32\u0c4b \u0c35\u0c3e\u0c24\u0c3e\u0c35\u0c30\u0c23\u0c02 \u0c0e\u0c32\u0c3e \u0c09\u0c02\u0c26\u0c3f?",
    "bn-IN": "\u09ae\u09c1\u09ae\u09cd\u09ac\u09be\u0987\u09af\u09bc\u09c7 \u0986\u09ac\u09b9\u09be\u0993\u09af\u09bc\u09be \u0995\u09c7\u09ae\u09a8?",
    "as-IN": "\u09ae\u09c1\u09ae\u09cd\u09ac\u09be\u0987\u09a4 \u09ac\u09a4\u09f0 \u0995\u09c7\u09a8\u09c7?",
}


class FakeExecutor:
    """Mocked-LLM seam: canned reply, no intermediate tool steps."""

    def __init__(self, output: str):
        self._output = output

    def invoke(self, _payload):
        return {"output": self._output, "intermediate_steps": []}


def _combined_transport(calls: list, *, stt_status: int = 200) -> httpx.MockTransport:
    """Mock every Sarvam surface: translate echoes input tagged per target
    (digits survive byte-identical), STT returns a canned transcript pair,
    TTS returns a short base64 WAV. Every hit is recorded in ``calls``."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/translate":
            body = json.loads(request.content.decode("utf-8"))
            calls.append(("translate", body))
            assert request.headers["api-subscription-key"] == "test-sarvam-key"
            assert body["numerals_format"] == "international"
            return httpx.Response(
                200,
                json={
                    "translated_text": f"[{body['target_language_code']}] {body['input']}"
                },
            )
        if path == "/speech-to-text":
            calls.append(("stt", bytes(request.content)))
            # Multipart shape: file bytes plus model plus mode, no key leaks.
            assert b"saaras:v3" in request.content
            assert b"transcribe" in request.content
            if stt_status != 200:
                return httpx.Response(stt_status, json={"error": "boom"})
            return httpx.Response(
                200,
                json={
                    "transcript": "What is the weather in Mumbai?",
                    "language_code": "hi-IN",
                },
            )
        if path == "/text-to-speech":
            body = json.loads(request.content.decode("utf-8"))
            calls.append(("tts", body))
            assert body["model"] == "bulbul:v3"
            assert body["speaker"] == "shubh"
            return httpx.Response(200, json={"audios": [FAKE_WAV_B64]})
        return httpx.Response(404, json={"error": f"unexpected path {path}"})

    return httpx.MockTransport(handler)


@pytest.fixture
def sarvam_key(monkeypatch):
    """Pin a sentinel Sarvam key so no test depends on the real .env value."""
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    from core.config import get_settings

    get_settings.cache_clear()
    try:
        yield "test-sarvam-key"
    finally:
        get_settings.cache_clear()
        sarvam_client.reset_transport()


def _route_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.parametrize("code", LANGUAGE_ROWS)
def test_chat_row_preserves_digits(code, sarvam_key):
    """Each remaining language round-trips with 29.5 intact and Green kept."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    fake = FakeExecutor(CANNED_ENGLISH_REPLY)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_multilingual_chat(
            QUERIES[code], location="Mumbai", language=code
        )
    assert "29.5" in result["reply"]
    assert result["alert_level"] == "Green"
    assert result["language"] == code
    # Exactly two translate calls: query -> en, en -> target reply.
    translate_calls = [body for kind, body in calls if kind == "translate"]
    assert [c["source_language_code"] for c in translate_calls] == [code, "en-IN"]
    assert translate_calls[1]["input"] == CANNED_ENGLISH_REPLY


def test_translate_model_routing_as_in_vs_hindi(sarvam_key):
    """as-IN either side pins sarvam-translate:v1; hi-IN stays mayura:v1."""
    calls: list = []
    transport = _combined_transport(calls)
    translate_text("hello", "en-IN", "as-IN", transport=transport)
    translate_text("hello", "as-IN", "en-IN", transport=transport)
    translate_text("hello", "en-IN", "hi-IN", transport=transport)
    translate_text("hello", "hi-IN", "en-IN", transport=transport)
    models = [body["model"] for kind, body in calls if kind == "translate"]
    assert models == [
        "sarvam-translate:v1",
        "sarvam-translate:v1",
        "mayura:v1",
        "mayura:v1",
    ]


async def test_transcribe_round_trip(sarvam_key):
    """WAV upload with mocked STT returns the transcript plus language echo."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    wav = b"RIFF\x24\x00\x00\x00WAVEfmt fake-upload-payload"
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/transcribe",
            files={"audio": ("test.wav", wav, "audio/wav")},
            data={"language_code": "hi-IN"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "What is the weather in Mumbai?"
    assert body["language_code"] == "hi-IN"
    assert any(kind == "stt" for kind, _ in calls)


async def test_speak_round_trip_returns_wav(sarvam_key):
    """Text plus hi-IN with mocked TTS returns non-empty audio/wav bytes."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/speak",
            json={"text": "Mumbai me mausam 29.5 C.", "language": "hi-IN"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content == FAKE_WAV_BYTES
    tts_calls = [body for kind, body in calls if kind == "tts"]
    assert len(tts_calls) == 1
    assert tts_calls[0]["language_code"] == "hi-IN"


async def test_speak_as_in_honest_422(sarvam_key):
    """as-IN speak never substitutes: HTTP 422 with a detail naming as-IN."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/speak",
            json={"text": "Mumbai weather.", "language": "as-IN"},
        )
    assert response.status_code == 422
    assert "as-IN" in response.json()["detail"]
    # No TTS provider hit for the unsupported voice.
    assert not any(kind == "tts" for kind, _ in calls)


async def test_transcribe_oversize_413_without_provider_call(sarvam_key):
    """A 3MB upload is rejected with 413 before any provider contact."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    big = b"\x00" * (3 * 1024 * 1024)
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/transcribe",
            files={"audio": ("big.wav", big, "audio/wav")},
            data={"language_code": "hi-IN"},
        )
    assert response.status_code == 413
    assert calls == []


async def test_transcribe_bad_content_type_422(sarvam_key):
    """A text/plain upload is rejected with 422 before provider contact."""
    calls: list = []
    sarvam_client.set_transport(_combined_transport(calls))
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/transcribe",
            files={"audio": ("note.txt", b"not audio", "text/plain")},
            data={"language_code": "hi-IN"},
        )
    assert response.status_code == 422
    assert not any(kind == "stt" for kind, _ in calls)


async def test_transcribe_outage_safe_502(sarvam_key):
    """Forced STT outage becomes a sanitized 502 with no key material."""
    sarvam_client.set_transport(_combined_transport([], stt_status=500))
    async with _route_client() as client:
        response = await client.post(
            "/api/voice/transcribe",
            files={"audio": ("test.wav", b"RIFFfake", "audio/wav")},
            data={"language_code": "hi-IN"},
        )
    assert response.status_code == 502
    text = response.text
    assert "test-sarvam-key" not in text
    assert "Traceback" not in text
