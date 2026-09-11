"""30-day climate-trend tests (Phase 8, Plan 01 tracer).

The LLM is kept out of the suite: every test serves the hand-authored
``open_meteo_archive_pune.json`` fixture through an ``imd_client``
``MockTransport`` — never live network and never OpenRouter. The
mocked-LLM number-match test patches ``services.agent._get_executor``
with a ``FakeExecutor`` mirroring ``tests/test_agent_grounding.py``.
"""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from services import agent as agent_module
from services.agent import process_chat
from tools import imd_client
from tools.weather import get_climate_trends

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_archive_pune.json"
)


def _mock_transport() -> httpx.MockTransport:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_archive():
    """Pin the archive fetch to the recorded Pune fixture; always reset after."""
    transport = _mock_transport()
    imd_client.set_transport(transport)
    try:
        yield transport
    finally:
        imd_client.reset_transport()


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so values are served
    deterministically regardless of test order."""
    from tools import weather as _weather_mod

    with _weather_mod._CACHE_LOCK:
        _weather_mod._CACHE.clear()
    try:
        yield
    finally:
        with _weather_mod._CACHE_LOCK:
            _weather_mod._CACHE.clear()


def _expected_from_fixture() -> dict:
    """Hand-computed aggregates straight from the fixture arrays."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    daily = fixture["daily"]
    times = daily["time"]
    tmax = daily["temperature_2m_max"]
    tmin = daily["temperature_2m_min"]
    precip = daily["precipitation_sum"]
    rain_sum = round(sum(precip), 2)
    means = [(hi + lo) / 2.0 for hi, lo in zip(tmax, tmin)]
    return {
        "rain_sum_mm": rain_sum,
        "temp_mean_c": round(sum(means) / len(means), 2),
        "temp_min_c": round(min(tmin), 2),
        "temp_max_c": round(max(tmax), 2),
        "wettest_day": times[precip.index(max(precip))],
        "driest_day": times[precip.index(min(precip))],
        "window_start": times[0],
        "window_end": times[-1],
    }


def test_mapping_aggregates_match_fixture():
    """map_archive_to_payload derives exact aggregates from fixture arrays."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mapped = imd_client.map_archive_to_payload(fixture, "Pune")
    expected = _expected_from_fixture()
    assert mapped["rain_sum_mm"] == expected["rain_sum_mm"] == 157.2
    assert mapped["temp_mean_c"] == expected["temp_mean_c"] == 27.02
    assert mapped["temp_min_c"] == expected["temp_min_c"] == 23.0
    assert mapped["temp_max_c"] == expected["temp_max_c"] == 32.0
    assert mapped["wettest_day"] == expected["wettest_day"] == "2026-08-23"
    assert mapped["driest_day"] == expected["driest_day"] == "2026-08-13"
    assert mapped["window_days"] == 30
    assert mapped["window_start"] == expected["window_start"] == "2026-08-12"
    assert mapped["window_end"] == expected["window_end"] == "2026-09-10"
    assert mapped["location"] == "Pune"
    assert "non-IMD" in mapped["source"]
    assert expected["wettest_day"] in mapped["deviation_note"]


def test_tool_json_contract(mock_archive):
    """get_climate_trends returns fixture aggregates as a JSON string."""
    expected = _expected_from_fixture()
    raw = get_climate_trends.invoke({"location": "Pune"})
    assert isinstance(raw, str)
    data = json.loads(raw)
    assert data["location"] == "Pune"
    assert data["rain_sum_mm"] == expected["rain_sum_mm"]
    assert data["temp_mean_c"] == expected["temp_mean_c"]
    assert data["wettest_day"] == expected["wettest_day"]
    assert data["driest_day"] == expected["driest_day"]
    assert data["window_days"] == 30
    assert data["window_start"] == expected["window_start"]
    assert data["window_end"] == expected["window_end"]
    assert "non-IMD" in data["source"]


def test_tool_fresh_stamps(mock_archive):
    """Tracer fresh path stamps cached/cache_age_s/stale without a cache."""
    raw = get_climate_trends.invoke({"location": "Pune"})
    data = json.loads(raw)
    assert data["cached"] is False
    assert data["cache_age_s"] == 0
    assert data["stale"] is False


class FakeExecutor:
    """Mocked-LLM seam: canned reply plus real tool JSON in steps."""

    def __init__(self, output: str, tool_json=None):
        self._output = output
        self._tool_json = tool_json

    def invoke(self, _payload):
        steps = [(None, self._tool_json)] if self._tool_json is not None else []
        return {"output": self._output, "intermediate_steps": steps}


def _grounded_trend_reply(data: dict) -> str:
    """Canned reply quoting real trend values plus window disclosure."""
    return (
        f"Pune past-30-day trend: {data['rain_sum_mm']} mm total rain, "
        f"mean {data['temp_mean_c']}°C, wettest {data['wettest_day']} "
        f"(non-IMD model data; source: {data['source']}). "
        f"{data['deviation_note']}"
    )


def test_mocked_llm_reply_quotes_exact_numbers(mock_archive):
    """Canned trend reply embeds the exact tool JSON numbers (D-04)."""
    raw = get_climate_trends.invoke({"location": "Pune"})
    data = json.loads(raw)
    fake = FakeExecutor(_grounded_trend_reply(data), raw)
    with patch.object(agent_module, "_get_executor", return_value=fake):
        result = process_chat(
            "Was this monsoon wetter than normal in Pune?", location="Pune"
        )
    assert str(data["rain_sum_mm"]) in result["reply"]
    assert str(data["temp_mean_c"]) in result["reply"]
    assert data["wettest_day"] in result["reply"]
    assert "non-IMD" in result["reply"]
    assert "30-day" in result["reply"]


def test_archive_outage_yields_stamped_fallback():
    """A transport-level outage yields a stamped mock fallback, never a raise."""

    def _failing(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("archive unreachable")

    imd_client.set_transport(httpx.MockTransport(_failing))
    try:
        raw = get_climate_trends.invoke({"location": "Pune"})
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)
    assert "mock" in data["source"]
    assert data["stale"] is True
