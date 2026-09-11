"""FCM secret-safety tests: key material never leaks into logs or responses.

Phase 10, T-10-04. Mirrors tests/test_multilingual_secrets.py: the private
key, access token, and device token all point at unique sentinel markers, a
500 outage is forced through the direct send path plus the send route plus
the check/status routes, then no sentinel may appear in the raised errors,
the response bodies, or captured log output. A sanitize_detail unit check
pins the shared redaction carryover.
"""

import json
import logging

import httpx
import pytest

from api.routes import sanitize_detail
from core.config import get_settings
from main import app
from services import alert_watcher, fcm_client
from tools import imd_client

SENTINEL_PRIVATE_KEY = "fake-private-key-SENTINEL-9f8e7d6c5b4a-UNIQUE"
SENTINEL_ACCESS_TOKEN = "fake-access-token-SENTINEL-1a2b3c4d5e6f-UNIQUE"
SENTINEL_DEVICE_TOKEN = "device-token-SENTINEL-7c3d9a1b2e4f-UNIQUE"


def _point_fcm_at_sentinels(tmp_path, monkeypatch) -> None:
    """Plant all three sentinels and clear cached singletons."""
    account = {
        "type": "service_account",
        "project_id": "test-project-123",
        "private_key_id": "fake-key-id-1",
        "private_key": SENTINEL_PRIVATE_KEY,
        "client_email": "fake@test-project-123.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fake",
    }
    sa_path = tmp_path / "sentinel-sa.json"
    sa_path.write_text(json.dumps(account), encoding="utf-8")
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_FILE", str(sa_path))
    get_settings.cache_clear()
    fcm_client.set_token_provider(lambda: SENTINEL_ACCESS_TOKEN)


def _assert_no_sentinels(*texts: str) -> None:
    for text in texts:
        assert SENTINEL_PRIVATE_KEY not in text
        assert SENTINEL_ACCESS_TOKEN not in text
        assert SENTINEL_DEVICE_TOKEN not in text


def _outage_transport(calls: list) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(500, json={"error": "simulated fcm outage"})

    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _isolate_fcm_secrets():
    """Reset watcher, weather cache, and FCM seams around every test."""
    from tools import weather as weather_mod

    alert_watcher.reset_for_tests()
    with weather_mod._CACHE_LOCK:
        weather_mod._CACHE.clear()
    imd_client.reset_transport()
    fcm_client.reset_transport()
    fcm_client.reset_token_provider()
    get_settings.cache_clear()
    try:
        yield
    finally:
        alert_watcher.reset_for_tests()
        with weather_mod._CACHE_LOCK:
            weather_mod._CACHE.clear()
        imd_client.reset_transport()
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
        get_settings.cache_clear()


def test_direct_send_outage_leaks_no_keys(tmp_path, monkeypatch, caplog):
    """Forced-500 direct send keeps all three sentinels out of errors/logs."""
    _point_fcm_at_sentinels(tmp_path, monkeypatch)
    calls: list = []
    fcm_client.set_transport(_outage_transport(calls))
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError) as exc_info:
                fcm_client.send_to_token(
                    SENTINEL_DEVICE_TOKEN, "t", "b", alert_level="Orange"
                )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert calls, "outage transport must have been hit"
    _assert_no_sentinels(str(exc_info.value), caplog.text)


async def test_send_route_outage_leaks_no_keys(tmp_path, monkeypatch, caplog):
    """502 send-route body and logs carry no sentinel material."""
    _point_fcm_at_sentinels(tmp_path, monkeypatch)
    calls: list = []
    fcm_client.set_transport(_outage_transport(calls))
    try:
        transport = httpx.ASGITransport(app=app)
        with caplog.at_level(logging.INFO):
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/alerts/send",
                    json={
                        "token": SENTINEL_DEVICE_TOKEN,
                        "title": "WeatherGPT Orange alert for Mumbai",
                        "body": "Stay alert.",
                        "alert_level": "Orange",
                        "location": "Mumbai",
                    },
                )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert response.status_code == 502
    _assert_no_sentinels(response.text, caplog.text)


async def test_check_route_outage_leaks_no_keys(tmp_path, monkeypatch, caplog):
    """Orange cycle against a 500 FCM stays 200 with clean bodies/logs."""
    _point_fcm_at_sentinels(tmp_path, monkeypatch)
    calls: list = []
    fcm_client.set_transport(_outage_transport(calls))

    def _orange(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "current": {
                    "temperature_2m": 30.0,
                    "relative_humidity_2m": 80,
                    "apparent_temperature": 32.0,
                    "precipitation": 0.0,
                    "weather_code": 95,
                    "pressure_msl": 1006.0,
                    "wind_speed_10m": 10.0,
                    "wind_direction_10m": 180,
                    "visibility": 6000.0,
                    "time": "2026-09-11T00:00:00Z",
                },
                "hourly": {"precipitation": [0.0] * 30},
            },
        )

    imd_client.set_transport(httpx.MockTransport(_orange))
    # Subscribe the sentinel device token first so the fan-out touches it.
    alert_watcher.subscribe(SENTINEL_DEVICE_TOKEN, ["alerts-mumbai"])
    try:
        transport = httpx.ASGITransport(app=app)
        with caplog.at_level(logging.INFO):
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.post("/api/alerts/check")
                status = await client.get("/api/alerts/status")
    finally:
        imd_client.reset_transport()
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert response.status_code == 200
    assert response.json()["checked"] == 18
    assert status.status_code == 200
    _assert_no_sentinels(response.text, status.text, caplog.text)


def test_sanitize_detail_redacts_known_keys(monkeypatch):
    """sanitize_detail still redacts the configured key carryover on all routes."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-SENTINEL-9f8e7d6c5b4a")
    monkeypatch.setenv("WEATHER_API_KEY", "wx-SENTINEL-1a2b3c4d5e6f")
    monkeypatch.setenv("SARVAM_API_KEY", "sv-SENTINEL-7c3d9a1b2e4f")
    get_settings.cache_clear()
    try:
        dirty = "boom sk-or-SENTINEL-9f8e7d6c5b4a plus wx-SENTINEL-1a2b3c4d5e6f"
        clean = sanitize_detail(dirty)
        assert "sk-or-SENTINEL-9f8e7d6c5b4a" not in clean
        assert "wx-SENTINEL-1a2b3c4d5e6f" not in clean
        assert "[REDACTED]" in clean
        assert "sv-SENTINEL-7c3d9a1b2e4f" not in sanitize_detail(
            "failure sv-SENTINEL-7c3d9a1b2e4f here"
        )
    finally:
        get_settings.cache_clear()
