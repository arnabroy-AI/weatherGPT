"""Alert watcher tests: registry plus dedup matrix plus cached seam plus routes.

Phase 10, D-01/D-02/D-03 (NOTF-01/NOTF-02). FCM HTTP is mocked in EVERY
test that touches send (httpx.MockTransport); the real service-account file
is never read. Weather upstream is mocked via imd_client.set_transport and
the tool TTL cache is cleared per test so hit counts stay deterministic.
"""

import json
import logging
from pathlib import Path

import httpx
import pytest

from core.config import get_settings
from main import app
from services import alert_watcher, fcm_client
from tools import imd_client

FAKE_PROJECT_ID = "test-project-123"
FAKE_ACCESS_TOKEN = "fake-access-token-9z"
FAKE_MESSAGE_NAME = f"projects/{FAKE_PROJECT_ID}/messages/msg-1"


def _fake_service_account() -> dict:
    return {
        "type": "service_account",
        "project_id": FAKE_PROJECT_ID,
        "private_key_id": "fake-key-id-1",
        "private_key": "fake-private-key-material-UNIQUE-7f3a",
        "client_email": f"fake@{FAKE_PROJECT_ID}.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fake",
    }


def _point_settings_at_fake_sa(tmp_path, monkeypatch) -> None:
    sa_path = tmp_path / "fake-sa.json"
    sa_path.write_text(json.dumps(_fake_service_account()), encoding="utf-8")
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_FILE", str(sa_path))
    get_settings.cache_clear()


def _inject_fake_auth() -> None:
    fcm_client.set_token_provider(lambda: FAKE_ACCESS_TOKEN)


def _orange_provider_payload() -> dict:
    """Provider JSON shaped so derive_alert_level yields Orange (code 95)."""
    return {
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
    }


def _green_provider_payload() -> dict:
    """Provider JSON shaped so derive_alert_level yields Green (code 0)."""
    payload = _orange_provider_payload()
    payload["current"]["weather_code"] = 0
    payload["current"]["wind_speed_10m"] = 5.0
    return payload


def _mock_weather_transport(counter: dict, payload: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        counter["hits"] += 1
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _isolate_watcher_state():
    """Reset watcher registry/dedup, weather cache, and FCM seams per test."""
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


def test_watch_constants_pin_phase_contract():
    """WATCH_CITIES holds 18 derived entries; Orange+Red only; 6h cooldown."""
    assert len(alert_watcher.WATCH_CITIES) == 18
    assert set(alert_watcher.DISPATCH_LEVELS) == {"Orange", "Red"}
    assert alert_watcher.COOLDOWN_S == 21600


def test_no_second_heuristic_in_watcher():
    """The threshold authority stays sole: no import, call, or redefinition."""
    source = Path(alert_watcher.__file__).read_text(encoding="utf-8")
    assert "from tools.imd_client import" not in source
    assert "import imd_client" not in source
    assert "imd_client.derive" not in source
    assert "def derive_alert_level" not in source
    assert "derive_alert_level(" not in source


def test_registry_subscribe_and_counts():
    """Subscribe registers tokens/topics; counts carry no token material."""
    result = alert_watcher.subscribe("device-token-abc123", ["alerts-mumbai"])
    assert result["token_suffix"] == "abc123"
    assert result["topics"] == ["alerts-mumbai"]
    counts = alert_watcher.registry_counts()
    assert counts["tokens"] == 1
    assert counts["topics"] == 1
    assert counts["subscriptions"] == 1
    assert "device-token-abc123" not in json.dumps(counts)


def test_registry_rejects_bad_shapes():
    """Empty token, overlong token, and bad topics raise ValueError."""
    with pytest.raises(ValueError):
        alert_watcher.subscribe("   ", ["alerts-mumbai"])
    with pytest.raises(ValueError):
        alert_watcher.subscribe("x" * 2049, ["alerts-mumbai"])
    with pytest.raises(ValueError):
        alert_watcher.subscribe("tok-1", ["bad topic!!"])
    with pytest.raises(ValueError):
        alert_watcher.subscribe("tok-1", ["x" * 129])


def test_dedup_matrix_first_orange_fires_repeat_suppressed():
    """First Orange fires; same level repeat inside 6h stays silent."""
    t0 = 1000.0
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0) is True
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0 + 100.0) is False


def test_dedup_matrix_upgrade_refires_immediately():
    """Orange-to-Red upgrade inside the cooldown re-fires."""
    t0 = 2000.0
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0) is True
    assert alert_watcher.should_dispatch("Mumbai", "Red", now=t0 + 200.0) is True


def test_dedup_matrix_green_yellow_never_fire():
    """Green and Yellow never dispatch, even on first sight."""
    assert alert_watcher.should_dispatch("Mumbai", "Green", now=3000.0) is False
    assert alert_watcher.should_dispatch("Mumbai", "Yellow", now=3000.0) is False
    assert alert_watcher.should_dispatch("Delhi", "Green", now=3000.0) is False


def test_dedup_matrix_downgrade_suppressed_inside_cooldown():
    """Red-to-Orange downgrade inside the cooldown stays silent."""
    t0 = 4000.0
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0) is True
    assert alert_watcher.should_dispatch("Mumbai", "Red", now=t0 + 100.0) is True
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0 + 200.0) is False


def test_dedup_matrix_cooldown_expiry_refires():
    """Same level after the 6h window fires again."""
    t0 = 5000.0
    assert alert_watcher.should_dispatch("Pune", "Orange", now=t0) is True
    assert (
        alert_watcher.should_dispatch("Pune", "Orange", now=t0 + 21600 + 1) is True
    )


def test_dedup_matrix_locations_are_independent():
    """Mumbai suppression never silences Delhi."""
    t0 = 6000.0
    assert alert_watcher.should_dispatch("Mumbai", "Orange", now=t0) is True
    assert alert_watcher.should_dispatch("Delhi", "Orange", now=t0 + 10.0) is True


def test_evaluate_city_orange_via_cached_seam_single_hit():
    """Orange surfaces through get_current_weather with one upstream hit."""
    counter = {"hits": 0}
    imd_client.set_transport(
        _mock_weather_transport(counter, _orange_provider_payload())
    )
    try:
        first = alert_watcher.evaluate_city("Mumbai")
        second = alert_watcher.evaluate_city("Mumbai")
    finally:
        imd_client.reset_transport()
    assert first is not None and first["alert_level"] == "Orange"
    assert second is not None and second["alert_level"] == "Orange"
    assert counter["hits"] == 1, f"expected 1 upstream hit, got {counter['hits']}"


def test_evaluate_city_failure_returns_none(monkeypatch):
    """A raising seam yields None (logged), never a raise."""
    class _BoomSeam:
        def invoke(self, payload):
            raise RuntimeError("simulated seam failure")

    monkeypatch.setattr(alert_watcher, "get_current_weather", _BoomSeam())
    result = alert_watcher.evaluate_city("Mumbai")
    assert result is None


def test_run_watch_cycle_all_orange_dispatches_18_then_dedups():
    """First Orange cycle dispatches 18; immediate repeat dispatches 0."""
    counter = {"hits": 0}
    imd_client.set_transport(
        _mock_weather_transport(counter, _orange_provider_payload())
    )
    calls: list = []

    def _fake_send(topic, title, body, level, location):
        calls.append(
            {
                "topic": topic,
                "title": title,
                "body": body,
                "level": level,
                "location": location,
            }
        )
        return "fake-name"

    try:
        first = alert_watcher.run_watch_cycle(send_fn=_fake_send, now=7000.0)
        second = alert_watcher.run_watch_cycle(send_fn=_fake_send, now=7100.0)
    finally:
        imd_client.reset_transport()
    assert first["checked"] == 18
    assert len(first["dispatched"]) == 18
    assert len(first["skipped"]) == 0
    assert len(calls) == 18
    assert calls[0]["topic"].startswith("alerts-")
    assert "WeatherGPT" in calls[0]["title"] and "Orange" in calls[0]["title"]
    assert len(calls[0]["body"]) <= 200
    assert second["checked"] == 18
    assert len(second["dispatched"]) == 0
    assert len(second["skipped"]) == 18


def test_run_watch_cycle_green_dispatches_nothing():
    """All-Green cycle checks 18 and dispatches 0 without calling send."""
    counter = {"hits": 0}
    imd_client.set_transport(
        _mock_weather_transport(counter, _green_provider_payload())
    )

    def _must_not_send(topic, title, body, level, location):
        raise AssertionError("send must not run for Green")

    try:
        report = alert_watcher.run_watch_cycle(send_fn=_must_not_send, now=8000.0)
    finally:
        imd_client.reset_transport()
    assert report["checked"] == 18
    assert report["dispatched"] == []
    assert len(report["skipped"]) == 18


def test_run_watch_cycle_single_city_failure_never_raises(monkeypatch):
    """One bad city is skipped; the cycle still reports checked 18."""
    real_evaluate = alert_watcher.evaluate_city

    def _flaky(city: str):
        if city == alert_watcher.WATCH_CITIES[0]:
            raise RuntimeError("simulated city failure")
        return real_evaluate(city)

    monkeypatch.setattr(alert_watcher, "evaluate_city", _flaky)
    counter = {"hits": 0}
    imd_client.set_transport(
        _mock_weather_transport(counter, _green_provider_payload())
    )
    calls: list = []
    try:
        report = alert_watcher.run_watch_cycle(
            send_fn=lambda *a: calls.append(a) or "x", now=9000.0
        )
    finally:
        imd_client.reset_transport()
    assert report["checked"] == 18
    assert len(report["dispatched"]) + len(report["skipped"]) == 18


def _route_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_route_subscribe_returns_suffix_only():
    """POST subscribe 200 echoes last-6 only, never the full token."""
    token = "device-token-SECRET-abcdef123456"
    async with _route_client() as client:
        response = await client.post(
            "/api/alerts/subscribe",
            json={"token": token, "topics": ["alerts-mumbai"]},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["token_suffix"] == token[-6:]
    assert body["topics"] == ["alerts-mumbai"]
    assert token not in response.text


async def test_route_subscribe_invalid_topic_422():
    """POST subscribe with a bad topic returns 422."""
    async with _route_client() as client:
        response = await client.post(
            "/api/alerts/subscribe",
            json={"token": "tok-1", "topics": ["bad topic!!"]},
        )
    assert response.status_code == 422


async def test_route_send_green_422():
    """POST send with Green never dispatches (422)."""
    async with _route_client() as client:
        response = await client.post(
            "/api/alerts/send",
            json={
                "token": "device-token-abc",
                "title": "t",
                "body": "b",
                "alert_level": "Green",
                "location": "Mumbai",
            },
        )
    assert response.status_code == 422


async def test_route_send_orange_token_200(tmp_path, monkeypatch):
    """POST send Orange to a token returns 200 carrying the message name."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {FAKE_ACCESS_TOKEN}"
        return httpx.Response(200, json={"name": FAKE_MESSAGE_NAME})

    fcm_client.set_transport(httpx.MockTransport(handler))
    try:
        async with _route_client() as client:
            response = await client.post(
                "/api/alerts/send",
                json={
                    "token": "device-token-abc",
                    "title": "WeatherGPT Orange alert for Mumbai",
                    "body": "Stay alert.",
                    "alert_level": "Orange",
                    "location": "Mumbai",
                },
            )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert response.status_code == 200
    assert response.json()["message_name"] == FAKE_MESSAGE_NAME


async def test_route_send_orange_topic_200(tmp_path, monkeypatch):
    """POST send Orange to a topic returns 200 carrying the message name."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"name": FAKE_MESSAGE_NAME})

    fcm_client.set_transport(httpx.MockTransport(handler))
    try:
        async with _route_client() as client:
            response = await client.post(
                "/api/alerts/send",
                json={
                    "topic": "alerts-mumbai",
                    "title": "WeatherGPT Orange alert for Mumbai",
                    "body": "Stay alert.",
                    "alert_level": "Orange",
                    "location": "Mumbai",
                },
            )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert response.status_code == 200
    assert response.json()["message_name"] == FAKE_MESSAGE_NAME


async def test_route_send_requires_exactly_one_target():
    """POST send with both or neither target returns 422."""
    payload_both = {
        "token": "tok",
        "topic": "alerts-mumbai",
        "title": "t",
        "body": "b",
        "alert_level": "Orange",
        "location": "Mumbai",
    }
    payload_neither = {
        "title": "t",
        "body": "b",
        "alert_level": "Orange",
        "location": "Mumbai",
    }
    async with _route_client() as client:
        both = await client.post("/api/alerts/send", json=payload_both)
        neither = await client.post("/api/alerts/send", json=payload_neither)
    assert both.status_code == 422
    assert neither.status_code == 422


async def test_route_check_returns_checked_18():
    """POST check runs the cycle server-side and reports checked 18."""
    counter = {"hits": 0}
    imd_client.set_transport(
        _mock_weather_transport(counter, _green_provider_payload())
    )
    try:
        async with _route_client() as client:
            response = await client.post("/api/alerts/check")
    finally:
        imd_client.reset_transport()
    assert response.status_code == 200
    assert response.json()["checked"] == 18


async def test_route_status_counts_no_token_material(caplog):
    """GET status returns counts plus flags with zero token bytes."""
    token = "device-token-STATUS-probe-xyz789"
    async with _route_client() as client:
        sub = await client.post(
            "/api/alerts/subscribe",
            json={"token": token, "topics": ["alerts-delhi"]},
        )
        assert sub.status_code == 200
        with caplog.at_level(logging.INFO):
            response = await client.get("/api/alerts/status")
    assert response.status_code == 200
    body = response.json()
    assert body["watch_cities"] == 18
    assert body["cooldown_hours"] == 6
    assert body["tokens"] >= 1
    assert isinstance(body["fcm_configured"], bool)
    assert token not in response.text
    assert token not in caplog.text
