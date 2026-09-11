"""Grounded-reply tests for the upgraded agent prompt (Phase 4, Plan 01).

The LLM is kept out of the suite: every test patches
``services.agent._get_executor`` with a ``FakeExecutor`` whose ``invoke``
returns a canned reply plus ``intermediate_steps`` carrying REAL tool JSON
(obtained by calling ``get_current_weather`` through an
``imd_client`` ``MockTransport`` serving the recorded fixture — never live
network and never OpenRouter).
"""

import json
import re
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from services import agent as agent_module
from services.agent import process_chat
from tools import imd_client
from tools.weather import get_current_weather

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"

ALERT_RE = re.compile(r"Alert:\s*(Green|Yellow|Orange|Red)")


def _mock_transport() -> httpx.MockTransport:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_open_meteo():
    """Pin the imd_client fetch to the recorded fixture; always reset after."""
    transport = _mock_transport()
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


def _grounded_reply(data: dict) -> str:
    """Canned reply quoting real tool values, disclosure, and Alert line."""
    return (
        f"Current weather in {data['location']}: {data['temperature_c']}°C, "
        f"{data['condition']} (non-IMD model data; source: {data['source']}). "
        f"{data['advisory']}\nAlert: {data['alert_level']}"
    )


def test_current_weather_reply_quotes_tool_values(mock_open_meteo):
    """Reply quotes the tool temperature_c value and condition string."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    fake = FakeExecutor(_grounded_reply(data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("What is the weather in Mumbai?", location="Mumbai")
    assert str(data["temperature_c"]) in result["reply"]
    assert data["condition"] in result["reply"]


def test_reply_contains_disclosure(mock_open_meteo):
    """Reply discloses non-IMD model data per the rewritten rule 6."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    fake = FakeExecutor(_grounded_reply(data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("What is the weather in Mumbai?", location="Mumbai")
    assert "non-IMD model data" in result["reply"]


def test_reply_alert_line_matches_regex(mock_open_meteo):
    """Reply ends with an Alert line matching the Phase 1 reply regex."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    fake = FakeExecutor(_grounded_reply(data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("What is the weather in Mumbai?", location="Mumbai")
    assert ALERT_RE.search(result["reply"]) is not None
    assert result["alert_level"] == data["alert_level"]


def test_unknown_location_asks_single_clarifying_question():
    """Unknown location with no context yields exactly one clarifying
    question and no city temperature values (no tool call made)."""
    fake = FakeExecutor("Which city or location should I check the weather for?")
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("What is the weather like?")
    assert result["reply"].count("?") == 1
    assert "°C" not in result["reply"]


def test_followup_with_location_is_grounded(mock_open_meteo):
    """A follow-up call carrying a location yields a grounded answer."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    fake = FakeExecutor(_grounded_reply(data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat("Mumbai", location="Mumbai")
    assert str(data["temperature_c"]) in result["reply"]
    assert "non-IMD model data" in result["reply"]
    assert ALERT_RE.search(result["reply"]) is not None
