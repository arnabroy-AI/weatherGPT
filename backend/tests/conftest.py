"""Shared pytest fixtures for the WeatherGPT backend test suite.

Sets up ``sys.path``, forces a dummy ``OPENROUTER_API_KEY`` so no real
secret is ever read during tests (T-01-01), and resets the settings and
agent-executor caches around every test for isolation.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure the repo root (which holds `main`, `api`, `core`, ...) is importable.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _dummy_keys_and_cache_reset(monkeypatch):
    """Force dummy secrets and reset cached singletons per test."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-dummy-key")

    from core.config import get_settings
    from services import agent as agent_module
    from api.throttle import reset_rate_limiter

    get_settings.cache_clear()
    agent_module.reset_agent_cache()
    reset_rate_limiter()
    try:
        yield
    finally:
        get_settings.cache_clear()
        agent_module.reset_agent_cache()
        reset_rate_limiter()
        os.environ.pop("OPENROUTER_API_KEY", None)
