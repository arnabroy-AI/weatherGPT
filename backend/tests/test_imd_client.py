"""Mapping + frozen-contract tests on the recorded Open-Meteo fixture.

All provider HTTP is served by httpx.MockTransport from
tests/fixtures/open_meteo_mumbai.json — no test touches the live network.
"""

import json
from pathlib import Path

import httpx
import pytest

from tools import imd_client
from tools.weather import get_current_weather

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"

FROZEN_KEYS = {
    "location",
    "observed_at_utc",
    "temperature_c",
    "feels_like_c",
    "humidity_pct",
    "condition",
    "rainfall_mm_last_24h",
    "wind_kph",
    "wind_direction",
    "pressure_hpa",
    "visibility_km",
    "source",
    "alert_level",
    "advisory",
}


def _fixture_payload() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _mock_transport() -> httpx.MockTransport:
    fixture = _fixture_payload()

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


def test_fixture_parses_with_expected_temperature():
    """Recorded fixture is valid JSON carrying the live Mumbai sample values."""
    data = _fixture_payload()
    assert data["current"]["temperature_2m"] == 26.1


def test_mapping(mock_open_meteo):
    """Fixture maps to all 14 frozen keys with Mumbai-sample values."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)

    assert FROZEN_KEYS <= set(data.keys()), f"missing keys: {FROZEN_KEYS - set(data.keys())}"
    assert data["temperature_c"] == 26.1
    assert data["feels_like_c"] == 31.8
    assert data["humidity_pct"] == 90
    assert data["wind_kph"] == 4.0
    assert data["wind_direction"] == "NNW"
    assert data["pressure_hpa"] == 1010.4
    assert data["observed_at_utc"] == "2026-09-10T19:30"
    assert data["alert_level"] == "Green"
    assert "open-meteo" in data["source"]


def test_contract_unchanged(mock_open_meteo):
    """Frozen seam holds: location echo + tool name unchanged on live path."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    assert data["location"] == "Mumbai"
    assert get_current_weather.name == "get_current_weather"


def test_tracer_pune_fixture_path(mock_open_meteo):
    """Pune invoke under MockTransport flows end-to-end to fixture values."""
    raw = get_current_weather.invoke({"location": "Pune"})
    data = json.loads(raw)
    assert data["temperature_c"] == 26.1
    assert data["wind_direction"] == "NNW"
    assert "open-meteo" in data["source"]
    assert data["alert_level"] == "Green"


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so transport-hit counts
    stay deterministic regardless of test order (T-02-04)."""
    from tools import weather as _weather_mod

    with _weather_mod._CACHE_LOCK:
        _weather_mod._CACHE.clear()
    try:
        yield
    finally:
        with _weather_mod._CACHE_LOCK:
            _weather_mod._CACHE.clear()


def _counting_transport(counter: dict) -> httpx.MockTransport:
    """MockTransport serving the recorded fixture while counting hits."""
    fixture = _fixture_payload()

    def handler(request: httpx.Request) -> httpx.Response:
        counter["hits"] += 1
        return httpx.Response(200, json=fixture)

    return httpx.MockTransport(handler)


def test_cache_hit():
    """Two identical Pune invokes trigger exactly one upstream call."""
    from tools import weather as weather_mod

    assert weather_mod.CACHE_TTL_S == 600
    counter = {"hits": 0}
    imd_client.set_transport(_counting_transport(counter))
    try:
        raw1 = get_current_weather.invoke({"location": "Pune"})
        raw2 = get_current_weather.invoke({"location": "Pune"})
    finally:
        imd_client.reset_transport()
    first = json.loads(raw1)
    second = json.loads(raw2)

    assert counter["hits"] == 1, f"expected 1 upstream call, got {counter['hits']}"
    assert first["cached"] is False
    assert first["cache_age_s"] == 0
    assert second["cached"] is True
    assert isinstance(second["cache_age_s"], int) and second["cache_age_s"] >= 0
    assert FROZEN_KEYS <= set(second.keys())
    assert second["temperature_c"] == 26.1


def test_ttl_expiry():
    """A pre-seeded expired Pune entry forces a refetch on next query."""
    import time

    from tools import weather as weather_mod

    base = imd_client.map_open_meteo_to_payload(_fixture_payload(), "Pune")
    now = time.monotonic()
    with weather_mod._CACHE_LOCK:
        weather_mod._CACHE["pune"] = {
            "expires": now - 1.0,
            "stored_at": now - 700.0,
            "payload": base,
        }
    counter = {"hits": 0}
    imd_client.set_transport(_counting_transport(counter))
    try:
        raw = get_current_weather.invoke({"location": "Pune"})
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert counter["hits"] == 1, f"expired entry must refetch, got {counter['hits']}"
    assert data["cached"] is False
    assert data["cache_age_s"] == 0
    assert "open-meteo" in data["source"]


def test_outage_fallback():
    """Killed provider still returns stamped disclosed fallback JSON fast."""
    import time

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated outage", request=request)

    imd_client.set_transport(httpx.MockTransport(handler))
    try:
        start = time.monotonic()
        raw = get_current_weather.invoke({"location": "Pune"})
        elapsed = time.monotonic() - start
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert data["source"] == "mock-imd-fallback"
    assert FROZEN_KEYS <= set(data.keys()), f"missing keys: {FROZEN_KEYS - set(data.keys())}"
    assert "live data unavailable" in data["advisory"]
    assert data["temperature_c"] == 29.5
    assert data["condition"] == "Light rain unavailable"
    assert data["alert_level"] == "Yellow"
    assert data["cached"] is False
    assert data["stale"] is True
    assert elapsed < 5.0, f"outage path took {elapsed:.2f}s, budget is 5s"

    # Fallback is never stored as fresh: a later healthy invoke refetches.
    counter = {"hits": 0}
    imd_client.set_transport(_counting_transport(counter))
    try:
        raw2 = get_current_weather.invoke({"location": "Pune"})
    finally:
        imd_client.reset_transport()
    data2 = json.loads(raw2)
    assert counter["hits"] == 1, "fallback must not pin the cache"
    assert data2["cached"] is False
    assert "open-meteo" in data2["source"]


def test_stale_on_error():
    """Expired Pune entry + dead provider serves stale data stamped stale."""
    import time

    from tools import weather as weather_mod

    base = imd_client.map_open_meteo_to_payload(_fixture_payload(), "Pune")
    now = time.monotonic()
    with weather_mod._CACHE_LOCK:
        weather_mod._CACHE["pune"] = {
            "expires": now - 1.0,
            "stored_at": now - 700.0,
            "payload": base,
        }

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated outage", request=request)

    imd_client.set_transport(httpx.MockTransport(handler))
    try:
        raw = get_current_weather.invoke({"location": "Pune"})
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert data["stale"] is True
    assert data["source"].endswith("+stale-fallback")
    assert "live data unavailable" in data["advisory"]
    # Proves the expired entry (26.1) was served, not the generic mock (29.5).
    assert data["temperature_c"] == 26.1
    assert FROZEN_KEYS <= set(data.keys())


def test_city_normalisation():
    """Mixed case plus surrounding whitespace resolves via the curated map."""
    from tools import weather as weather_mod

    assert len(weather_mod.CITY_COORDS) == 18
    assert "nashik" in weather_mod.CITY_COORDS
    assert "pune" in weather_mod.CITY_COORDS
    counter = {"hits": 0}
    imd_client.set_transport(_counting_transport(counter))
    try:
        raw1 = get_current_weather.invoke({"location": "  MUMBAI "})
        raw2 = get_current_weather.invoke({"location": "mumbai"})
    finally:
        imd_client.reset_transport()
    first = json.loads(raw1)
    second = json.loads(raw2)

    assert first["location"] == "Mumbai"
    assert second["location"] == "Mumbai"
    assert counter["hits"] == 1, (
        f"normalised lookups must share one cache entry, got {counter['hits']} hits"
    )
    assert "open-meteo" in first["source"]


def test_best_guess(mock_open_meteo):
    """Unknown locations return disclosed Mumbai best-guess data, never a refusal."""
    raw = get_current_weather.invoke({"location": "Atlantis XYZ"})
    data = json.loads(raw)

    assert data["resolved_location"] == "Mumbai (best guess)"
    assert data["requested_location"] == "Atlantis XYZ"
    assert "best-guess" in data["advisory"]
    assert data["advisory"].startswith(
        "Showing best-guess data for Mumbai instead of Atlantis XYZ."
    )
    assert data["location"] == "Mumbai"
    assert FROZEN_KEYS <= set(data.keys())


def test_key_missing_live_path(mock_open_meteo, monkeypatch):
    """Empty WEATHER_API_KEY still serves the live keyless path (D-02)."""
    from core.config import get_settings

    from tools import weather as weather_mod

    monkeypatch.setattr(get_settings(), "WEATHER_API_KEY", "")
    with weather_mod._CACHE_LOCK:
        weather_mod._CACHE.clear()
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)

    assert "open-meteo" in data["source"]
    assert data["location"] == "Mumbai"
    assert FROZEN_KEYS <= set(data.keys())


def test_no_key_leak(monkeypatch, caplog):
    """Key material never appears in fallback JSON or logs (sanitize_detail mirror)."""
    import logging

    from core.config import get_settings

    from tools import weather as weather_mod

    monkeypatch.setattr(get_settings(), "WEATHER_API_KEY", "SECRET_PROBE_42")
    with weather_mod._CACHE_LOCK:
        weather_mod._CACHE.clear()

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated outage", request=request)

    imd_client.set_transport(httpx.MockTransport(handler))
    try:
        with caplog.at_level(logging.ERROR):
            raw = get_current_weather.invoke({"location": "Mumbai"})
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert "SECRET_PROBE_42" not in raw
    assert "SECRET_PROBE_42" not in caplog.text
    assert data["source"] == "mock-imd-fallback"
    assert FROZEN_KEYS <= set(data.keys())
