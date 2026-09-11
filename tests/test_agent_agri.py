"""Agri/climate grounding tests for the curated advisory slice (Phase 4, Plan 02).

The LLM is kept out of the suite: every grounding test patches
``services.agent._get_executor`` with a ``FakeExecutor`` whose ``invoke``
returns a canned reply (curated advisory text plus REAL tool values)
with ``intermediate_steps`` carrying REAL tool JSON obtained by calling
``get_current_weather`` / ``get_weather_forecast`` through an
``imd_client`` ``MockTransport`` serving recorded fixtures — never live
network and never OpenRouter. Mirrors the Plan 01 harness in
``tests/test_agent_grounding.py``.
"""

import json
import re
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from services import agent as agent_module
from services.agent import SYSTEM_PROMPT, process_chat
from services.agri_advisories import get_advisory
from tools import imd_client
from tools.weather import get_current_weather, get_weather_forecast

CURRENT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"
FORECAST_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_forecast_mumbai.json"
)

ALERT_RE = re.compile(r"Alert:\s*(Green|Yellow|Orange|Red)")

_REFUSAL_PHRASES = ("cannot help", "unable to help", "cannot advise", "do not know")


def _routing_transport() -> httpx.MockTransport:
    """Serve the forecast fixture for daily params, the current fixture else."""
    current = json.loads(CURRENT_FIXTURE_PATH.read_text(encoding="utf-8"))
    forecast = json.loads(FORECAST_FIXTURE_PATH.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        if "daily" in request.url.params:
            return httpx.Response(200, json=forecast)
        return httpx.Response(200, json=current)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_open_meteo():
    """Pin the imd_client fetch to the recorded fixtures; always reset after."""
    transport = _routing_transport()
    imd_client.set_transport(transport)
    try:
        yield transport
    finally:
        imd_client.reset_transport()


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so fixture values are
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


def _agri_reply(curated: str, data: dict) -> str:
    """Canned reply combining curated text with live tool values."""
    return (
        f"{curated} Live now in {data['location']}: {data['temperature_c']}°C, "
        f"{data['condition']} (non-IMD model data; source: {data['source']}). "
        f"{data['advisory']}\nAlert: {data['alert_level']}"
    )


# --- Curated lookup tests (selected by `-k curated`) ---


def test_curated_lookup_paddy_kharif():
    """Paddy/kharif lookup returns a non-empty paddy note with non-IMD."""
    text = get_advisory("paddy", "kharif")
    assert isinstance(text, str) and text.strip()
    assert "non-IMD" in text
    assert "paddy" in text.lower()


def test_curated_lookup_case_and_season_cues():
    """Lookup normalizes case/whitespace; monsoon reads as the kharif note."""
    kharif = get_advisory("paddy", "kharif")
    monsoon = get_advisory("  PADDY sowing ", " Monsoon ")
    assert monsoon == kharif
    assert "non-IMD" in monsoon
    wheat = get_advisory("Wheat", "rabi")
    assert "wheat" in wheat.lower() and "non-IMD" in wheat


def test_curated_lookup_unknown_crop_fallback():
    """Unknown crops yield the generic best-effort fallback, never empty."""
    text = get_advisory("dragonfruit", "kharif")
    assert isinstance(text, str) and text.strip()
    assert "non-IMD" in text
    lowered = text.lower()
    assert not any(phrase in lowered for phrase in _REFUSAL_PHRASES)


# --- Mocked-LLM agri grounding tests ---


def test_paddy_sowing_nashik_grounds_curated_plus_live(mock_open_meteo):
    """Nashik paddy reply carries curated paddy text plus the live temp."""
    raw = get_current_weather.invoke({"location": "Nashik"})
    data = json.loads(raw)
    curated = get_advisory("paddy", "kharif")
    fake = FakeExecutor(_agri_reply(curated, data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat(
            "When should I sow paddy in Nashik?", location="Nashik"
        )
    assert "transplant 20-25 day nursery seedlings" in result["reply"]
    assert str(data["temperature_c"]) in result["reply"]
    assert "non-IMD model data" in result["reply"]
    assert ALERT_RE.search(result["reply"]) is not None
    assert result["alert_level"] == data["alert_level"]


def test_unknown_crop_best_effort_no_refusal(mock_open_meteo):
    """An unknown-crop question gets a best-effort answer, not a refusal."""
    raw = get_current_weather.invoke({"location": "Pune"})
    data = json.loads(raw)
    curated = get_advisory("dragonfruit")
    fake = FakeExecutor(_agri_reply(curated, data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat(
            "Can I grow dragonfruit near Pune this season?", location="Pune"
        )
    assert "General farm advisory" in result["reply"]
    assert str(data["temperature_c"]) in result["reply"]
    lowered = result["reply"].lower()
    assert not any(phrase in lowered for phrase in _REFUSAL_PHRASES)


def test_climate_summary_grounds_forecast_days(mock_open_meteo):
    """A climate summary question grounds in forecast JSON day values."""
    raw = get_weather_forecast.invoke({"location": "Nashik"})
    fdata = json.loads(raw)
    assert fdata["forecast_available"] is True
    first = fdata["forecast_days"][0]
    reply = (
        f"Climate outlook for {fdata['location']}: {first['date']} high "
        f"{first['temp_max_c']}°C, {first['condition']} "
        f"(non-IMD model data; source: {fdata['source']}). "
        f"{fdata['alert_line']}"
    )
    fake = FakeExecutor(reply, raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat(
            "Summarise the 5-day climate outlook for Nashik.", location="Nashik"
        )
    assert first["date"] in result["reply"]
    assert str(first["temp_max_c"]) in result["reply"]
    assert fdata["alert_line"] in result["reply"]


def test_system_prompt_agri_rules_reference_tools_and_curated_base():
    """SYSTEM_PROMPT agri rules direct both live tools plus the curated base.

    The current-weather tool is named literally; the forecast tool is
    directed via its canonical rule 2 reference, preserving Phase 3's
    pinned single literal mention of `get_weather_forecast`. _TOOLS intact.
    """
    assert "`get_current_weather`" in SYSTEM_PROMPT
    assert "`get_weather_forecast`" in SYSTEM_PROMPT
    assert "forecast tool from rule 2" in SYSTEM_PROMPT
    assert "sowing" in SYSTEM_PROMPT
    assert "curated" in SYSTEM_PROMPT.lower()
    assert "best-effort" in SYSTEM_PROMPT.lower()
    assert SYSTEM_PROMPT.count("get_weather_forecast") == 1
    # Phase 8 Plan 01: the trends tool joins _TOOLS alongside the two
    # existing entries (D-04 minimal wiring); agri rules themselves unchanged.
    assert len(agent_module._TOOLS) == 3
