"""Tracer tests for the 5-day forecast slice (Phase 3, Plan 01).

All provider HTTP is served by httpx.MockTransport from recorded fixtures —
no test touches the live network.
"""

import json
import re
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from tools import imd_client
from tools.weather import get_current_weather, get_weather_forecast

FORECAST_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_forecast_mumbai.json"
)
CURRENT_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"
)

# Phase 1 Alert reply regex plus the Phase 3 day tag in trailing parens (D-04).
ALERT_LINE_RE = re.compile(r"Alert: (Green|Yellow|Orange|Red) \([A-Za-z]{3}\)")

DAY_KEYS = {
    "date",
    "temp_min_c",
    "temp_max_c",
    "rain_chance_pct",
    "condition",
    "alert_level",
}

_SEVERITY = {"Green": 0, "Yellow": 1, "Orange": 2, "Red": 3}


def _forecast_fixture() -> dict:
    return json.loads(FORECAST_FIXTURE_PATH.read_text(encoding="utf-8"))


def _current_fixture() -> dict:
    return json.loads(CURRENT_FIXTURE_PATH.read_text(encoding="utf-8"))


def _routing_transport(counter: dict, kill_daily: bool = False) -> httpx.MockTransport:
    """Serve the forecast fixture for daily params, the current fixture else.

    Records the last upstream query params so clamp tests can prove the
    clamped day count reached the provider.
    """
    forecast = _forecast_fixture()
    current = _current_fixture()

    def handler(request: httpx.Request) -> httpx.Response:
        counter["hits"] += 1
        counter["last_params"] = dict(request.url.params)
        if "daily" in request.url.params:
            if kill_daily:
                raise httpx.ConnectError("simulated daily outage", request=request)
            return httpx.Response(200, json=forecast)
        return httpx.Response(200, json=current)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_forecast_transport():
    """Pin the imd_client fetch to the recorded fixtures; always reset after."""
    counter = {"hits": 0, "last_params": {}}
    imd_client.set_transport(_routing_transport(counter))
    try:
        yield counter
    finally:
        imd_client.reset_transport()


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so transport-hit counts
    stay deterministic regardless of test order (mirrors test_imd_client.py)."""
    from tools import weather as _weather_mod

    with _weather_mod._CACHE_LOCK:
        _weather_mod._CACHE.clear()
    try:
        yield
    finally:
        imd_client.reset_transport()
        with _weather_mod._CACHE_LOCK:
            _weather_mod._CACHE.clear()


def test_mapping_day_shape():
    """map_forecast_to_payload returns 5 entries with sane per-day fields."""
    mapped = imd_client.map_forecast_to_payload(_forecast_fixture(), "Mumbai", 5)

    assert len(mapped["days"]) == 5
    assert len(mapped["forecast_days"]) == 5
    for day in mapped["days"]:
        assert DAY_KEYS <= set(day.keys()), f"missing keys: {DAY_KEYS - set(day.keys())}"
        assert day["temp_min_c"] <= day["temp_max_c"]
        assert 0 <= day["rain_chance_pct"] <= 100
        assert isinstance(day["condition"], str) and day["condition"]
        assert day["alert_level"] in _SEVERITY


def test_mapping_worst_day_line():
    """Severe fixture day surfaces Orange in worst_alert and the Alert line."""
    mapped = imd_client.map_forecast_to_payload(_forecast_fixture(), "Mumbai", 5)

    severest = max(
        (day["alert_level"] for day in mapped["days"]),
        key=lambda level: _SEVERITY[level],
    )
    assert mapped["worst_alert"] == severest == "Orange"
    assert mapped["alert_line"].startswith("Alert: Orange ")
    assert ALERT_LINE_RE.search(mapped["alert_line"]), mapped["alert_line"]
    expected_tag = datetime.fromisoformat(mapped["worst_day"]).strftime("%a")
    assert mapped["alert_line"].endswith(f"({expected_tag})")
    assert "open-meteo" in mapped["source"] and "non-IMD" in mapped["source"]


def test_mapping_unknown_code():
    """Unknown weathercode maps to 'Unknown (code N)' without raising."""
    fixture = _forecast_fixture()
    fixture["daily"] = dict(fixture["daily"])
    fixture["daily"]["weathercode"] = [777, 2, 1, 3, 0]

    mapped = imd_client.map_forecast_to_payload(fixture, "Mumbai", 5)

    assert mapped["days"][0]["condition"] == "Unknown (code 777)"
    assert mapped["days"][1]["condition"] == "Partly cloudy"


def test_end_to_end_forecast_mumbai(mock_forecast_transport):
    """get_weather_forecast for Mumbai returns 5 alerted days plus Alert line."""
    data = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))

    assert data["forecast_available"] is True
    assert len(data["forecast_days"]) == 5
    for day in data["forecast_days"]:
        assert DAY_KEYS <= set(day.keys())
        assert day["temp_min_c"] <= day["temp_max_c"]
        assert 0 <= day["rain_chance_pct"] <= 100
        assert day["condition"]
        assert day["alert_level"] in _SEVERITY
    severest = max(
        (day["alert_level"] for day in data["forecast_days"]),
        key=lambda level: _SEVERITY[level],
    )
    assert data["worst_alert"] == severest
    assert ALERT_LINE_RE.search(data["alert_line"]), data["alert_line"]
    assert "open-meteo" in data["source"] and "non-IMD" in data["source"]
    assert get_weather_forecast.name == "get_weather_forecast"


def test_cache_hit(mock_forecast_transport):
    """Two identical Mumbai invokes trigger exactly one upstream call."""
    counter = mock_forecast_transport

    first = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    second = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))

    assert counter["hits"] == 1, f"expected 1 upstream call, got {counter['hits']}"
    assert first["cached"] is False
    assert second["cached"] is True
    assert isinstance(second["cache_age_s"], int) and second["cache_age_s"] >= 0
    assert second["forecast_days"] == first["forecast_days"]


def test_outage_partial():
    """Killed daily transport returns current-weather values, no mock days."""
    counter = {"hits": 0, "last_params": {}}
    imd_client.set_transport(_routing_transport(counter, kill_daily=True))
    try:
        data = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    finally:
        imd_client.reset_transport()

    assert data["forecast_days"] == []
    assert data["forecast_available"] is False
    assert "forecast unavailable" in data["note"]
    assert "Mumbai" in data["note"]
    # Live current-weather values flow through (recorded 26.1 sample).
    assert data["temperature_c"] == 26.1
    assert data["feels_like_c"] == 31.8

    # Partial payloads are never cached: a healthy retry refetches upstream.
    imd_client.set_transport(_routing_transport(counter))
    try:
        retry = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    finally:
        imd_client.reset_transport()
    assert retry["forecast_available"] is True
    assert len(retry["forecast_days"]) == 5


def test_days_clamp(mock_forecast_transport):
    """Days below 3 clamp to 3 and above 5 clamp to 5, end to end."""
    counter = mock_forecast_transport

    low = json.loads(get_weather_forecast.invoke({"location": "Mumbai", "days": 2}))
    assert len(low["forecast_days"]) == 3
    assert low["days"] == 3
    assert counter["last_params"].get("forecast_days") == "3"

    high = json.loads(get_weather_forecast.invoke({"location": "Mumbai", "days": 9}))
    assert len(high["forecast_days"]) == 5
    assert high["days"] == 5
    assert counter["last_params"].get("forecast_days") == "5"


def test_cache_isolation(mock_forecast_transport):
    """Forecast and current entries never share cache state."""
    counter = mock_forecast_transport

    get_weather_forecast.invoke({"location": "Mumbai"})
    get_current_weather.invoke({"location": "Mumbai"})
    assert counter["hits"] == 2, f"expected 2 upstream calls, got {counter['hits']}"

    # Re-invoking both serves cache: no further upstream calls.
    get_weather_forecast.invoke({"location": "Mumbai"})
    get_current_weather.invoke({"location": "Mumbai"})
    assert counter["hits"] == 2, "forecast/current entries must cache independently"

    # Day count is part of the key: days=3 refetches once, then caches.
    three = json.loads(get_weather_forecast.invoke({"location": "Mumbai", "days": 3}))
    assert len(three["forecast_days"]) == 3
    assert counter["hits"] == 3
    get_weather_forecast.invoke({"location": "Mumbai", "days": 3})
    assert counter["hits"] == 3
