"""Cache/TTL/partial-fallback/secret-safety tests for the forecast path.

Phase 3, Plan 03 — hardens the Plan 01 `get_weather_forecast` contract per
D-06 (10-min cache keyed location-plus-days) and D-07 (partial current-only
fallback with an honest note). Mirrors the Phase 2 cache test idioms from
tests/test_imd_client.py against the daily fixture from Plan 01.

All provider HTTP is served by httpx.MockTransport from recorded fixtures —
no test touches the live network. Zero source changes.

Variance vs plan (recorded in 03-03-SUMMARY.md): the plan specified
``stale true`` for the live-current partial; the actual Plan 01 contract
sets ``stale`` False on that branch (``partial.setdefault("stale", False)``
over the fresh current mapping — the data served IS fresh current
conditions, so False is semantically correct). The ``stale True`` stamp
applies to the expired-entry branch (``_decorate_stale``) and to the
generic mock fallback (``_fallback_payload``), not to the live partial.
This suite asserts the actual contract.
"""

import json
import logging
import time
from pathlib import Path

import httpx
import pytest

from tools import imd_client
from tools.weather import get_weather_forecast

FORECAST_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_forecast_mumbai.json"
)
CURRENT_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_mumbai.json"
)


def _forecast_fixture() -> dict:
    return json.loads(FORECAST_FIXTURE_PATH.read_text(encoding="utf-8"))


def _current_fixture() -> dict:
    return json.loads(CURRENT_FIXTURE_PATH.read_text(encoding="utf-8"))


def _routing_transport(counter: dict, kill_daily: bool = False) -> httpx.MockTransport:
    """Serve the forecast fixture for daily params, the current fixture else."""
    forecast = _forecast_fixture()
    current = _current_fixture()

    def handler(request: httpx.Request) -> httpx.Response:
        counter["hits"] += 1
        if "daily" in request.url.params:
            if kill_daily:
                raise httpx.ConnectError("simulated daily outage", request=request)
            return httpx.Response(200, json=forecast)
        return httpx.Response(200, json=current)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_forecast_transport():
    """Pin the imd_client fetch to the recorded fixtures; always reset after."""
    counter = {"hits": 0}
    imd_client.set_transport(_routing_transport(counter))
    try:
        yield counter
    finally:
        imd_client.reset_transport()


@pytest.fixture(autouse=True)
def _isolate_weather_cache():
    """Clear the tool TTL cache around every test so transport-hit counts
    stay deterministic regardless of test order (mirrors test_forecast.py)."""
    from tools import weather as _weather_mod

    with _weather_mod._CACHE_LOCK:
        _weather_mod._CACHE.clear()
    try:
        yield
    finally:
        imd_client.reset_transport()
        with _weather_mod._CACHE_LOCK:
            _weather_mod._CACHE.clear()


def test_cache_hit_identical_invokes(mock_forecast_transport):
    """Two identical Mumbai 5-day invokes trigger exactly one upstream call."""
    counter = mock_forecast_transport

    first = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    second = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))

    assert counter["hits"] == 1, f"expected 1 upstream call, got {counter['hits']}"
    assert first["cached"] is False
    assert first["cache_age_s"] == 0
    assert second["cached"] is True
    assert isinstance(second["cache_age_s"], int) and second["cache_age_s"] >= 0
    assert second["forecast_days"] == first["forecast_days"]
    assert second["forecast_available"] is True


def test_cache_key_includes_days(mock_forecast_transport):
    """Mumbai 5-day vs Mumbai 3-day are separate entries (days in the key)."""
    counter = mock_forecast_transport

    five = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    three = json.loads(
        get_weather_forecast.invoke({"location": "Mumbai", "days": 3})
    )

    assert counter["hits"] == 2, f"expected 2 upstream calls, got {counter['hits']}"
    assert len(five["forecast_days"]) == 5
    assert len(three["forecast_days"]) == 3
    # Repeat of the 3-day variant serves cache: no further upstream call.
    get_weather_forecast.invoke({"location": "Mumbai", "days": 3})
    assert counter["hits"] == 2, "days-variant entry must cache independently"


def test_cache_normalisation(mock_forecast_transport):
    """Case/whitespace variants share one normalised cache entry."""
    counter = mock_forecast_transport

    first = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    second = json.loads(get_weather_forecast.invoke({"location": "  mumbai  "}))

    assert counter["hits"] == 1, (
        f"normalised lookups must share one cache entry, got {counter['hits']} hits"
    )
    assert first["location"] == "Mumbai"
    assert second["cached"] is True
    assert second["forecast_days"] == first["forecast_days"]


def test_ttl_expiry_forces_refetch(mock_forecast_transport):
    """A pre-seeded expired Mumbai 5-day entry forces a refetch on next query."""
    from tools import weather as weather_mod

    counter = mock_forecast_transport

    # Seed a real entry via one healthy invoke, then expire it in place.
    json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    assert counter["hits"] == 1
    cache_key = ("forecast", "mumbai", 5)
    with weather_mod._CACHE_LOCK:
        entry = weather_mod._CACHE[cache_key]
        entry["expires"] = time.monotonic() - 1.0
        entry["stored_at"] = time.monotonic() - 700.0

    data = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))

    assert counter["hits"] == 2, f"expired entry must refetch, got {counter['hits']}"
    assert data["cached"] is False
    assert data["cache_age_s"] == 0
    assert data["forecast_available"] is True
    assert len(data["forecast_days"]) == 5


def test_outage_partial_no_pinning():
    """Killed daily transport returns partial current-only output fast.

    Asserts the actual Plan 01 partial contract: empty forecast_days,
    forecast_available False, an honest "forecast unavailable" note, live
    current temperature fields, and — variance vs plan text — stale False
    (the served current conditions are fresh, not expired). A healthy retry
    refetches exactly once, proving the partial was never pinned.
    """
    counter = {"hits": 0}
    imd_client.set_transport(_routing_transport(counter, kill_daily=True))
    try:
        start = time.monotonic()
        raw = get_weather_forecast.invoke({"location": "Mumbai"})
        elapsed = time.monotonic() - start
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert data["forecast_days"] == []
    assert data["forecast_available"] is False
    assert "forecast unavailable" in data["note"]
    assert "Mumbai" in data["note"]
    # Live current-weather values flow through (recorded 26.1/31.8 sample).
    assert data["temperature_c"] == 26.1
    assert data["feels_like_c"] == 31.8
    assert data["stale"] is False
    assert data["cached"] is False
    assert elapsed < 5.0, f"outage path took {elapsed:.2f}s, budget is 5s"

    # Partial payloads are never cached: a healthy retry refetches upstream.
    hits_before = counter["hits"]
    imd_client.set_transport(_routing_transport(counter))
    try:
        retry = json.loads(get_weather_forecast.invoke({"location": "Mumbai"}))
    finally:
        imd_client.reset_transport()
    assert counter["hits"] == hits_before + 1, "partial must not pin the cache"
    assert retry["forecast_available"] is True
    assert len(retry["forecast_days"]) == 5


def test_no_secret_leak_on_forecast_path(monkeypatch, caplog):
    """Key material never appears in forecast JSON or logs (T-03-07)."""
    from core.config import get_settings

    monkeypatch.setattr(get_settings(), "WEATHER_API_KEY", "SECRET_PROBE_42")

    counter = {"hits": 0}
    imd_client.set_transport(_routing_transport(counter, kill_daily=True))
    try:
        with caplog.at_level(logging.ERROR):
            raw = get_weather_forecast.invoke({"location": "Mumbai"})
    finally:
        imd_client.reset_transport()
    data = json.loads(raw)

    assert "SECRET_PROBE_42" not in raw
    assert "SECRET_PROBE_42" not in caplog.text
    # Sanity: the probe run still returned the honest partial shape.
    assert data["forecast_days"] == []
    assert data["forecast_available"] is False
    assert "forecast unavailable" in data["note"]
