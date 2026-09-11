"""FCM dispatch tracer proof (Phase 10, D-02, NOTF-01).

Proves the token path plus the topic path through FCM v1 with a fully
mocked transport: an Orange fixture pinned through the sole threshold
authority (``derive_alert_level``) dispatches on both paths with Bearer
auth and the reply carries the FCM message name. Negative paths pin the
missing-file disabled signal, forced-500 key cleanliness (sentinel test),
and empty-target ValueErrors.

Safety: FCM HTTP is mocked in EVERY test (httpx.MockTransport) — the real
``backend/fcm-service-account.json`` is never read and no live network I/O
occurs. The service-account file is faked under ``tmp_path`` and pointed
at via the ``FCM_SERVICE_ACCOUNT_FILE`` setting plus ``cache_clear``.
"""

import json
import logging

import httpx
import pytest

from core.config import get_settings
from services import fcm_client
from tools.imd_client import derive_alert_level

FAKE_PROJECT_ID = "test-project-123"
FAKE_PRIVATE_KEY = "fake-private-key-material-UNIQUE-7f3a"
FAKE_ACCESS_TOKEN = "fake-access-token-9z"
FAKE_MESSAGE_NAME = f"projects/{FAKE_PROJECT_ID}/messages/msg-1"

EXPECTED_SEND_PATH = f"/v1/projects/{FAKE_PROJECT_ID}/messages:send"


def _fake_service_account() -> dict:
    """Unique-marker fake service-account JSON (never the real key file)."""
    return {
        "type": "service_account",
        "project_id": FAKE_PROJECT_ID,
        "private_key_id": "fake-key-id-1",
        "private_key": FAKE_PRIVATE_KEY,
        "client_email": f"fake@{FAKE_PROJECT_ID}.iam.gserviceaccount.com",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fake",
    }


@pytest.fixture(autouse=True)
def _clean_fcm_state():
    """Mirror the conftest isolation discipline for the FCM seams."""
    try:
        yield
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
        get_settings.cache_clear()


def _point_settings_at_fake_sa(tmp_path, monkeypatch) -> dict:
    """Write the fake service account under tmp_path and repoint settings."""
    account = _fake_service_account()
    sa_path = tmp_path / "fake-sa.json"
    sa_path.write_text(json.dumps(account), encoding="utf-8")
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_FILE", str(sa_path))
    get_settings.cache_clear()
    return account


def _inject_fake_auth(monkeypatch):
    """Inject the fake bearer via the token-provider seam (no crypto)."""
    fcm_client.set_token_provider(lambda: FAKE_ACCESS_TOKEN)


def _assert_no_key_material(*texts: str) -> None:
    for text in texts:
        assert FAKE_PRIVATE_KEY not in text
        assert FAKE_ACCESS_TOKEN not in text


def test_orange_authority_pin():
    """Sole-threshold-authority carryover: code 95 derives Orange."""
    assert derive_alert_level(95) == "Orange"


def test_token_path_dispatch(tmp_path, monkeypatch):
    """Orange Mumbai payload dispatches on the token path with Bearer auth."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth(monkeypatch)
    level = derive_alert_level(95)
    assert level == "Orange"

    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == EXPECTED_SEND_PATH
        assert request.headers["authorization"] == f"Bearer {FAKE_ACCESS_TOKEN}"
        body = json.loads(request.content.decode("utf-8"))
        seen.update(body)
        message = body["message"]
        assert message["token"] == "device-token-abc"
        assert "topic" not in message
        assert message["notification"]["title"]
        assert message["notification"]["body"]
        assert message["data"]["alert_level"] == "Orange"
        return httpx.Response(200, json={"name": FAKE_MESSAGE_NAME})

    fcm_client.set_transport(httpx.MockTransport(handler))
    try:
        name = fcm_client.send_to_token(
            "device-token-abc",
            "Orange alert for Mumbai",
            "Thunderstorm likely in Mumbai (non-IMD model data). Stay alert.",
            alert_level=level,
            location="Mumbai",
        )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert name == FAKE_MESSAGE_NAME
    assert seen["message"]["data"]["location"] == "Mumbai"


def test_topic_path_dispatch(tmp_path, monkeypatch):
    """Orange Mumbai payload dispatches on the topic path with Bearer auth."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth(monkeypatch)
    level = derive_alert_level(95)
    assert level == "Orange"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == EXPECTED_SEND_PATH
        assert request.headers["authorization"] == f"Bearer {FAKE_ACCESS_TOKEN}"
        body = json.loads(request.content.decode("utf-8"))
        message = body["message"]
        assert message["topic"] == "alerts-mumbai"
        assert "token" not in message
        assert message["notification"]["title"]
        assert message["notification"]["body"]
        assert message["data"]["alert_level"] == "Orange"
        assert message["data"]["location"] == "Mumbai"
        return httpx.Response(200, json={"name": FAKE_MESSAGE_NAME})

    fcm_client.set_transport(httpx.MockTransport(handler))
    try:
        name = fcm_client.send_to_topic(
            "alerts-mumbai",
            "Orange alert for Mumbai",
            "Thunderstorm likely in Mumbai (non-IMD model data). Stay alert.",
            alert_level=level,
            location="Mumbai",
        )
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert name == FAKE_MESSAGE_NAME


def test_missing_file_disables_cleanly(tmp_path, monkeypatch):
    """Absent service-account file: loader returns None, send says not configured."""
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_FILE", str(tmp_path / "does-not-exist.json"))
    get_settings.cache_clear()
    assert fcm_client.load_service_account() is None
    with pytest.raises(RuntimeError, match="not configured"):
        fcm_client.send_to_token("device-token-abc", "t", "b")


def test_forced_500_leaks_no_key_material(tmp_path, monkeypatch, caplog):
    """Forced-500 sentinel: raised error plus logs carry no key material."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "simulated fcm outage"})

    fcm_client.set_transport(httpx.MockTransport(handler))
    try:
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError) as exc_info:
                fcm_client.send_to_token("device-token-abc", "t", "b")
    finally:
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    _assert_no_key_material(str(exc_info.value), caplog.text)


def test_empty_token_raises_value_error(tmp_path, monkeypatch):
    """Empty device token is rejected before any send."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth(monkeypatch)
    with pytest.raises(ValueError):
        fcm_client.send_to_token("   ", "t", "b")


def test_empty_topic_raises_value_error(tmp_path, monkeypatch):
    """Empty topic is rejected before any send."""
    _point_settings_at_fake_sa(tmp_path, monkeypatch)
    _inject_fake_auth(monkeypatch)
    with pytest.raises(ValueError):
        fcm_client.send_to_topic("", "t", "b")
