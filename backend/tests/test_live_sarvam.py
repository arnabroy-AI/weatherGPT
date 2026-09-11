"""Opt-in live Sarvam test — skipped unless RUN_LIVE_SARVAM=1.

The default suite never touches the Sarvam network (MockTransport only). To
run for real::

    RUN_LIVE_SARVAM=1 SARVAM_API_KEY=<real-key> python -m pytest tests/test_live_sarvam.py -q

Tiny fixed text mirroring scripts/live_vendor_probe.py (en-IN -> hi-IN
translate proof). The real key is captured at module import (before
conftest's dummy-key fixture runs) and restored inside the test so the live
call is genuinely authenticated. The key is never logged or printed.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_SARVAM") != "1",
    reason="Live Sarvam test disabled by default; set RUN_LIVE_SARVAM=1 to run.",
)

_REAL_KEY_AT_IMPORT = os.getenv("SARVAM_API_KEY", "")

LIVE_TEXT = "What is the weather today"


def test_live_sarvam_translate_en_to_hi(monkeypatch):
    """Single short benign translate against the real Sarvam API."""
    if not _REAL_KEY_AT_IMPORT:
        pytest.skip("RUN_LIVE_SARVAM=1 set but no real SARVAM_API_KEY present.")
    monkeypatch.setenv("SARVAM_API_KEY", _REAL_KEY_AT_IMPORT)
    from core.config import get_settings
    from services import sarvam_client

    get_settings.cache_clear()
    sarvam_client.reset_transport()
    try:
        translated = sarvam_client.translate_text(LIVE_TEXT, "en-IN", "hi-IN")
    finally:
        get_settings.cache_clear()
        sarvam_client.reset_transport()
    assert isinstance(translated, str) and translated.strip()
