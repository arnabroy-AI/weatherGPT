"""Named-gap degradation + secret-safety + Alert-regex gate (Phase 4, Plan 03).

Covers AGNT-04 / D-07 / D-08: a tool-data outage mid-chat yields a
still-200 graceful reply that names the failed piece (current conditions
vs forecast) and states what still works, while an LLM outage keeps
failing loudly (RuntimeError -> route 502, per tests/test_error_contract.py).

The LLM is kept out of the suite: every process_chat test patches
``services.agent._get_executor`` with a ``FakeExecutor`` whose ``invoke``
returns a canned degraded reply plus ``intermediate_steps`` carrying REAL
tool JSON (fallback / partial payloads from ``tools.weather`` served
through an ``imd_client`` ``MockTransport`` — never live network and never
OpenRouter). Mirrors the Plan 01/02 harness.
"""

import inspect
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from core.config import get_settings
from services import agent as agent_module
from services.agent import process_chat
from tools import imd_client
from tools.weather import _fallback_payload, get_weather_forecast

CURRENT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"


@pytest.fixture
def mock_current_only():
    """Serve the recorded current fixture; fail daily (forecast) fetches.

    This drives ``get_weather_forecast`` down its real outage branch:
    the forecast fetch raises, the current fetch succeeds, and the tool
    returns the honest partial current-only payload (D-07).
    """
    current = json.loads(CURRENT_FIXTURE_PATH.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        if "daily" in request.url.params:
            raise httpx.ConnectError("simulated forecast outage")
        return httpx.Response(200, json=current)

    transport = httpx.MockTransport(handler)
    imd_client.set_transport(transport)
    try:
        yield transport
    finally:
        imd_client.reset_transport()


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so outage payloads are
    served deterministically regardless of test order."""
    from tools import weather as _weather_mod

    with _weather_mod._CACHE_LOCK:
        _weather_mod._CACHE.clear()
    try:
        yield
    finally:
        with _weather_mod._CACHE_LOCK:
            _weather_mod._CACHE.clear()


class FakeExecutor:
    """Mocked-LLM seam: canned reply plus real tool JSON in steps."""

    def __init__(self, output: str, tool_json=None):
        self._output = output
        self._tool_json = tool_json

    def invoke(self, _payload):
        steps = [(None, self._tool_json)] if self._tool_json is not None else []
        return {"output": self._output, "intermediate_steps": steps}


def test_system_prompt_degraded_rules_name_gaps():
    """SYSTEM_PROMPT rule 10 distinguishes current vs forecast failure.

    Pins the degraded-mode vocabulary (fallback / stale /
    forecast-unavailable markers, named pieces, what-still-works, no
    refusals) and preserves Phase 3's single literal mention of the
    forecast tool (referenced via its rule 2 number instead).
    """
    prompt = agent_module.SYSTEM_PROMPT
    lowered = prompt.lower()
    assert "fallback" in lowered
    assert "stale" in lowered
    assert "forecast-unavailable" in lowered or "forecast unavailable" in lowered
    assert "current conditions" in lowered
    assert "forecast" in lowered
    assert "what still works" in lowered or "still works" in lowered
    assert "refusal" in lowered
    assert prompt.count("get_weather_forecast") == 1


def test_fallback_current_names_gap_and_states_what_works():
    """Fallback-marked current JSON -> reply names current conditions as
    unavailable, states what still works, and quotes usable values.

    The agent-level contract for tool-data gaps is pass-through (no
    exception: the route keeps returning still-200, per D-07).
    """
    raw = json.dumps(_fallback_payload("Mumbai"))
    data = json.loads(raw)
    assert data["stale"] is True
    assert "live data unavailable" in data["advisory"].lower()
    reply = (
        "Current conditions are unavailable for Mumbai "
        "(live data unavailable; showing fallback values). "
        "Here is what still works: the forecast path plus cached values "
        f"— fallback now {data['temperature_c']}°C, {data['condition']} "
        "(non-IMD model data)."
    )
    fake = FakeExecutor(reply, raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("What is the weather in Mumbai?", location="Mumbai")
    lowered = result["reply"].lower()
    assert "current conditions" in lowered and "unavailable" in lowered
    assert "still works" in lowered
    assert str(data["temperature_c"]) in result["reply"]
    assert data["condition"] in result["reply"]


def test_partial_forecast_names_forecast_gap_plus_current(mock_current_only):
    """Forecast-unavailable partial JSON -> reply names forecast as
    unavailable, states what still works, and quotes current values."""
    raw = get_weather_forecast.invoke({"location": "Mumbai"})
    fdata = json.loads(raw)
    assert fdata["forecast_available"] is False
    assert "forecast unavailable" in fdata["note"].lower()
    reply = (
        f"Forecast is unavailable for {fdata['location']} ({fdata['note']}). "
        "Here is what still works: current conditions — "
        f"{fdata['temperature_c']}°C, {fdata['condition']} (non-IMD model data)."
    )
    fake = FakeExecutor(reply, raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat(
            "Give me the 5-day forecast for Mumbai.", location="Mumbai"
        )
    lowered = result["reply"].lower()
    assert "forecast" in lowered and "unavailable" in lowered
    assert "still works" in lowered
    assert str(fdata["temperature_c"]) in result["reply"]
    assert fdata["condition"] in result["reply"]


def test_executor_exception_still_raises_runtime_error():
    """A forced executor failure propagates as RuntimeError (never a 200).

    This is the LLM-outage path from Phase 1: retry once, then fail
    loudly so the route keeps returning 502.
    """
    failing_executor = MagicMock()
    failing_executor.invoke.side_effect = ConnectionError("upstream down")
    with patch.object(agent_module, "_get_executor", return_value=failing_executor):
        with pytest.raises(RuntimeError):
            process_chat("Will it rain in Mumbai?", location="Mumbai")
    assert failing_executor.invoke.call_count == agent_module.LLM_MAX_ATTEMPTS == 2


def test_prompt_and_curated_content_carry_no_secrets(monkeypatch):
    """SYSTEM_PROMPT and the curated advisory module contain no key material.

    Mirrors tests/test_secrets.py: both keys are pointed at sentinel
    markers, then the live settings values AND the sentinel prefixes are
    asserted absent from all static prompt/curated text.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-SENTINEL-9f8e7d6c5b4a-UNIQUE")
    monkeypatch.setenv("WEATHER_API_KEY", "wx-SENTINEL-1a2b3c4d5e6f-UNIQUE")
    get_settings.cache_clear()
    try:
        import services.agri_advisories as agri_module

        prompt_text = agent_module.SYSTEM_PROMPT
        curated_text = inspect.getsource(agri_module)
        for text in (prompt_text, curated_text):
            assert "sk-or" not in text
            assert "sk-test" not in text
            assert "sk-or-SENTINEL-9f8e7d6c5b4a-UNIQUE" not in text
            assert "wx-SENTINEL-1a2b3c4d5e6f-UNIQUE" not in text
        settings = get_settings()
        for secret in (settings.OPENROUTER_API_KEY, settings.WEATHER_API_KEY):
            if secret:
                assert secret not in prompt_text
                assert secret not in curated_text
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("level", ["Green", "Yellow", "Orange", "Red"])
def test_alert_lines_match_derive_regex(level):
    """Every Alert line the upgraded prompt can emit resolves via
    _derive_alert_level: single-day plain lines and worst-day lines with
    weekday parens (e.g. `Alert: Orange (Sat)`)."""
    single_day = (
        f"Clear spells over Mumbai, 29.5°C (non-IMD model data).\nAlert: {level}"
    )
    worst_day = (
        f"Worst day 2026-09-13 high 31.2°C (non-IMD model data).\nAlert: {level} (Sat)"
    )
    assert agent_module._derive_alert_level(single_day) == level
    assert agent_module._derive_alert_level(worst_day) == level
