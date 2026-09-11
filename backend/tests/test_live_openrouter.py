"""Opt-in live OpenRouter test — skipped unless WEATHERGPT_LIVE=1 (D-04).

The default suite never touches the network. To run for real::

    WEATHERGPT_LIVE=1 OPENROUTER_API_KEY=<real-key> python -m pytest tests/test_live_openrouter.py -q

The real key is captured at module import (before conftest's dummy-key fixture
runs) and restored inside the test so the live call is genuinely authenticated.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("WEATHERGPT_LIVE") != "1",
    reason="Live OpenRouter test disabled by default; set WEATHERGPT_LIVE=1 to run.",
)

_REAL_KEY_AT_IMPORT = os.getenv("OPENROUTER_API_KEY", "")


def test_live_openrouter_short_query(monkeypatch):
    """Single short benign query against the real agent path."""
    if not _REAL_KEY_AT_IMPORT:
        pytest.skip("WEATHERGPT_LIVE=1 set but no real OPENROUTER_API_KEY present.")
    monkeypatch.setenv("OPENROUTER_API_KEY", _REAL_KEY_AT_IMPORT)
    from core.config import get_settings
    from services import agent as agent_module

    get_settings.cache_clear()
    agent_module.reset_agent_cache()
    try:
        result = agent_module.process_chat(
            message="Reply with exactly the word sunny.", location="Mumbai"
        )
    finally:
        get_settings.cache_clear()
        agent_module.reset_agent_cache()
    assert isinstance(result["reply"], str) and result["reply"]
    assert result["alert_level"] in ("Green", "Yellow", "Orange", "Red")
