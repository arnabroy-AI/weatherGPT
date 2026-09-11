"""Opt-in live FCM test — skipped unless RUN_LIVE_FCM=1.

The default suite never touches the FCM network (MockTransport only). To
run for real::

    RUN_LIVE_FCM=1 FCM_SERVICE_ACCOUNT_FILE=<real-sa> python -m pytest tests/test_live_fcm.py -q

Requires the ``google-auth`` opt-in (``pip install google-auth``) plus a
valid service-account file. Sends one benign Orange topic payload with
``validate_only`` so FCM validates the shape and nothing delivers. The real
key is captured at module import (before conftest's dummy-key fixture runs)
and restored inside the test so the live call is genuinely authenticated.
The key is never logged or printed.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_FCM") != "1",
    reason="Live FCM test disabled by default; set RUN_LIVE_FCM=1 to run.",
)

_REAL_SA_AT_IMPORT = os.getenv("FCM_SERVICE_ACCOUNT_FILE", "")


def test_live_fcm_validate_only_orange_topic(monkeypatch):
    """Single benign Orange topic payload in validate_only posture."""
    if not _REAL_SA_AT_IMPORT:
        pytest.skip("RUN_LIVE_FCM=1 set but no real FCM_SERVICE_ACCOUNT_FILE present.")
    pytest.importorskip("google.auth", reason="google-auth opt-in not installed.")
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_FILE", _REAL_SA_AT_IMPORT)
    from core.config import get_settings
    from services import fcm_client

    get_settings.cache_clear()
    fcm_client.reset_transport()
    fcm_client.reset_token_provider()
    try:
        account = fcm_client.load_service_account()
        if account is None:
            pytest.skip("Live FCM service-account file missing; nothing to validate.")
        project_id = account["project_id"]
        access_token = fcm_client.get_access_token(account)
        import httpx

        url = fcm_client.FCM_SEND_URL_TEMPLATE.format(project_id=project_id)
        payload = {
            "message": {
                "topic": "alerts-mumbai",
                "notification": {
                    "title": "WeatherGPT Orange alert for Mumbai",
                    "body": "Live validate_only probe; no delivery.",
                },
                "data": {"alert_level": "Orange", "location": "Mumbai"},
            },
            "validate_only": True,
        }
        with httpx.Client(timeout=fcm_client.REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
    finally:
        get_settings.cache_clear()
        fcm_client.reset_transport()
        fcm_client.reset_token_provider()
    assert response.status_code == 200, f"validate_only probe got {response.status_code}"
