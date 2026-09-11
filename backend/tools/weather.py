"""Weather tools exposed to the LangChain agent.

`get_current_weather` returns live Open-Meteo current weather behind the
IMD-shaped seam (Phase 2, D-09) — keyless model data with non-authenticity
disclosed in `source`/advisory. Tool name, signature, and return contract
(JSON string, 14 frozen keys) stay the same.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone

from langchain_core.tools import tool

from core.config import get_settings
from tools import imd_client

logger = logging.getLogger(__name__)

# D-07 curated city -> lat/lon (frozen at plan time via Open-Meteo geocoding).
# Exactly 18 majors: metros plus state capitals plus Nashik and Pune (D-07/D-08).
CITY_COORDS = {
    "mumbai": (19.07283, 72.88261),
    "delhi": (28.6139, 77.2090),
    "pune": (18.5204, 73.8567),
    "nashik": (19.9975, 73.7898),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "bhopal": (23.2599, 77.4126),
    "patna": (25.5941, 85.1376),
    "thiruvananthapuram": (8.5241, 76.9366),
    "kochi": (9.9312, 76.2673),
    "guwahati": (26.1445, 91.7362),
    "chandigarh": (30.7333, 76.7794),
    "srinagar": (34.0837, 74.7973),
}

# Maximum location input length before use (Phase 1 schema carryover).
_MAX_LOCATION_CHARS = 120

# Nearest-map fallback anchor for unmappable input (D-08: guess + disclose).
_FALLBACK_CITY = "mumbai"

# D-03: process-local 10-minute TTL cache keyed by normalised location.
# Never stores fallback/error payloads as fresh (T-02-04).
CACHE_TTL_S = 600
_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()

# Literal disclosure sentence appended on every degraded answer (D-05).
_FALLBACK_NOTE = "Note: live data unavailable; showing fallback values."


def _fallback_payload(location_display: str) -> dict:
    """Disclosed mock-shaped payload when the live fetch fails (D-04/D-05)."""
    return {
        "location": location_display,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "temperature_c": 29.5,
        "feels_like_c": 32.0,
        "humidity_pct": 78,
        "condition": "Light rain unavailable",
        "rainfall_mm_last_24h": 12.4,
        "wind_kph": 18.0,
        "wind_direction": "SW",
        "pressure_hpa": 1006,
        "visibility_km": 6.0,
        "source": "mock-imd-fallback",
        "alert_level": "Yellow",
        "advisory": f"{_FALLBACK_NOTE} Live data unavailable for "
        f"{location_display}; showing fallback values (non-IMD model data). "
        "Light rain possible. Carry an umbrella.",
        "cached": False,
        "cache_age_s": 0,
        "stale": True,
    }


def _decorate_fresh(payload: dict) -> dict:
    """Stamp a just-fetched payload as a fresh (non-cached) answer."""
    out = dict(payload)
    out["cached"] = False
    out["cache_age_s"] = 0
    out["stale"] = False
    return out


def _decorate_hit(payload: dict, age_s: int) -> dict:
    """Stamp a cached payload served within TTL."""
    out = dict(payload)
    out["cached"] = True
    out["cache_age_s"] = max(0, int(age_s))
    out["stale"] = False
    return out


def _decorate_stale(payload: dict, age_s: int) -> dict:
    """Stamp an expired entry served only because upstream failed (D-04/D-05)."""
    out = dict(payload)
    out["cached"] = True
    out["cache_age_s"] = max(0, int(age_s))
    out["stale"] = True
    out["source"] = f"{out.get('source', '')}+stale-fallback"
    out["advisory"] = f"{out.get('advisory', '')} {_FALLBACK_NOTE}".strip()
    return out


def _try_parse_latlon(value: str):
    """Parse a raw 'lat,lon' string into in-range floats, else None (T-02-07)."""
    parts = value.split(",")
    if len(parts) != 2:
        return None
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return (lat, lon)


@tool("get_current_weather")
def get_current_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: City, district, or 'lat,lon' string (e.g. 'Mumbai').

    Returns:
        A JSON string with temperature, humidity, condition, wind,
        and an alert level. Live Open-Meteo model data (non-IMD);
        disclosed fallback values when the fetch fails.
    """
    settings = get_settings()
    _ = settings.WEATHER_API_KEY  # Reserved for the future IMD path; keyless live path (D-02).

    # Cap input at 120 chars before use (Phase 1 schema carryover).
    raw = ((location or "Unknown")[:_MAX_LOCATION_CHARS]).strip() or "Unknown"
    lookup_key = raw.lower()

    coords = CITY_COORDS.get(lookup_key)
    guessed = False
    if coords is not None:
        location_display = raw.title()
    else:
        parsed = _try_parse_latlon(raw)
        if parsed is not None:
            coords = parsed
            location_display = raw
        else:
            # D-08: best-guess nearest-map anchor AND disclose the guess.
            # Never refuse and never substitute silently.
            coords = CITY_COORDS[_FALLBACK_CITY]
            guessed = True
            location_display = _FALLBACK_CITY.title()
    latitude, longitude = coords

    def _apply_guess_note(payload: dict) -> dict:
        if guessed:
            base_advisory = str(payload.get("advisory", ""))
            payload["requested_location"] = raw
            payload["resolved_location"] = f"{_FALLBACK_CITY.title()} (best guess)"
            payload["advisory"] = (
                f"Showing best-guess data for {_FALLBACK_CITY.title()} "
                f"instead of {raw}. {base_advisory}"
            ).strip()
            # Location always reflects the resolved city actually queried.
            payload["location"] = _FALLBACK_CITY.title()
        return payload

    # D-03 cache hit path: serve the unexpired entry with disclosure stamps.
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(lookup_key)
    if entry is not None and now < entry["expires"]:
        age_s = int(now - entry["stored_at"])
        return json.dumps(_apply_guess_note(_decorate_hit(entry["payload"], age_s)))

    try:
        provider_data = imd_client.fetch_open_meteo(latitude, longitude)
        payload = imd_client.map_open_meteo_to_payload(provider_data, location_display)
    except Exception:
        # Outage taxonomy (RESEARCH.md): httpx.HTTPError/timeouts plus
        # ValueError/KeyError/TypeError (and RuntimeError) from schema
        # mismatch all land here — imd_client already wraps transport
        # failures. Log full server-side; user payload stays sanitized
        # (T-02-05: never keys, URLs, or tracebacks).
        logger.exception("get_current_weather live fetch failed")
        # Stale-only-on-error: serve the expired entry (if any) stamped
        # with age; otherwise the generic mock-shaped fallback. Neither
        # branch is stored as a fresh entry (T-02-04).
        with _CACHE_LOCK:
            stale_entry = _CACHE.get(lookup_key)
        if stale_entry is not None:
            age_s = int(time.monotonic() - stale_entry["stored_at"])
            return json.dumps(
                _apply_guess_note(_decorate_stale(stale_entry["payload"], age_s))
            )
        return json.dumps(_apply_guess_note(_fallback_payload(location_display)))

    # Fresh success: store the base payload (no disclosure stamps stored),
    # then return it stamped fresh. Fallbacks never reach this store.
    stored_at = time.monotonic()
    base_payload = dict(payload)
    with _CACHE_LOCK:
        _CACHE[lookup_key] = {
            "expires": stored_at + CACHE_TTL_S,
            "stored_at": stored_at,
            "payload": base_payload,
        }
    return json.dumps(_apply_guess_note(_decorate_fresh(base_payload)))


# Phase 3 (D-01/D-06): day-count bounds for the forecast tool. The tool
# signature defaults to 5 and clamps callers into the 3..5 range.
_FORECAST_DAYS_DEFAULT = 5
_FORECAST_DAYS_MIN = 3
_FORECAST_DAYS_MAX = 5


def _clamp_forecast_days(value) -> int:
    """Coerce a days argument into the 3..5 range; garbage yields 5."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        return _FORECAST_DAYS_DEFAULT
    return max(_FORECAST_DAYS_MIN, min(_FORECAST_DAYS_MAX, count))


def _apply_forecast_guess_note(payload: dict, raw: str, guessed: bool) -> dict:
    """Mirror the current-tool best-guess disclosure on forecast payloads."""
    if guessed:
        note = (
            f"Showing best-guess data for {_FALLBACK_CITY.title()} "
            f"instead of {raw}."
        )
        payload["requested_location"] = raw
        payload["resolved_location"] = f"{_FALLBACK_CITY.title()} (best guess)"
        advisory = str(payload.get("advisory", ""))
        payload["advisory"] = f"{note} {advisory}".strip() if advisory else note
        # Location always reflects the resolved city actually queried.
        payload["location"] = _FALLBACK_CITY.title()
    return payload


def _partial_forecast_payload(
    latitude: float,
    longitude: float,
    location_display: str,
    raw: str,
    guessed: bool,
) -> dict:
    """Current-weather values plus an honest forecast-unavailable note (D-07).

    Never synthesizes mock forecast days. Never stored in the cache (T-03-03).
    """
    try:
        provider_data = imd_client.fetch_open_meteo(latitude, longitude)
        current = imd_client.map_open_meteo_to_payload(
            provider_data, location_display
        )
    except Exception:
        logger.exception("get_weather_forecast current fallback failed")
        current = _fallback_payload(location_display)
    partial = dict(current)
    partial["forecast_days"] = []
    partial["forecast_available"] = False
    partial["note"] = (
        f"forecast unavailable for {location_display} "
        "(non-IMD model data); showing current conditions only."
    )
    partial["cached"] = False
    partial["cache_age_s"] = 0
    partial.setdefault("stale", False)
    return _apply_forecast_guess_note(partial, raw, guessed)


@tool("get_weather_forecast")
def get_weather_forecast(location: str, days: int = 5) -> str:
    """Get the day-wise weather forecast for a location.

    Args:
        location: City, district, or 'lat,lon' string (e.g. 'Mumbai').
        days: Day count requested, clamped to the 3..5 range (default 5).

    Returns:
        A JSON string with per-day min/max, rain chance, condition,
        per-day alert levels, and a worst-day Alert line. Live Open-Meteo
        model data (non-IMD); a partial current-only payload with an honest
        note when the forecast fetch fails.
    """
    settings = get_settings()
    _ = settings.WEATHER_API_KEY  # Reserved for the future IMD path; keyless live path.

    # Cap input at 120 chars before use (Phase 1 schema carryover).
    raw = ((location or "Unknown")[:_MAX_LOCATION_CHARS]).strip() or "Unknown"
    lookup_key = raw.lower()

    coords = CITY_COORDS.get(lookup_key)
    guessed = False
    if coords is not None:
        location_display = raw.title()
    else:
        parsed = _try_parse_latlon(raw)
        if parsed is not None:
            coords = parsed
            location_display = raw
        else:
            # Best-guess nearest-map anchor AND disclose the guess.
            # Never refuse and never substitute silently.
            coords = CITY_COORDS[_FALLBACK_CITY]
            guessed = True
            location_display = _FALLBACK_CITY.title()
    latitude, longitude = coords

    day_count = _clamp_forecast_days(days)
    # D-06/T-03-03: tuple key namespaces forecast entries so they can never
    # collide with the current tool's plain-string location keys.
    cache_key = ("forecast", lookup_key, day_count)

    # Cache hit path: serve the unexpired entry with disclosure stamps.
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(cache_key)
    if entry is not None and now < entry["expires"]:
        age_s = int(now - entry["stored_at"])
        return json.dumps(
            _apply_forecast_guess_note(
                _decorate_hit(entry["payload"], age_s), raw, guessed
            )
        )

    try:
        provider_data = imd_client.fetch_forecast_open_meteo(
            latitude, longitude, day_count
        )
        mapped = imd_client.map_forecast_to_payload(
            provider_data, location_display, day_count
        )
    except Exception:
        # Forecast outage (D-07): serve the expired entry stamped stale when
        # one exists, else the partial current-only payload. Neither branch
        # is stored as a fresh entry (T-03-03).
        logger.exception("get_weather_forecast live fetch failed")
        with _CACHE_LOCK:
            stale_entry = _CACHE.get(cache_key)
        if stale_entry is not None:
            age_s = int(time.monotonic() - stale_entry["stored_at"])
            return json.dumps(
                _apply_forecast_guess_note(
                    _decorate_stale(stale_entry["payload"], age_s), raw, guessed
                )
            )
        return json.dumps(
            _partial_forecast_payload(
                latitude, longitude, location_display, raw, guessed
            )
        )

    payload = {
        "location": mapped["location"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "forecast_days": mapped["days"],
        "forecast_available": True,
        "days": day_count,
        "worst_alert": mapped["worst_alert"],
        "worst_day": mapped["worst_day"],
        "alert_line": mapped["alert_line"],
        "source": mapped["source"],
    }

    # Fresh success only: store the base payload, return it stamped fresh.
    stored_at = time.monotonic()
    base_payload = dict(payload)
    with _CACHE_LOCK:
        _CACHE[cache_key] = {
            "expires": stored_at + CACHE_TTL_S,
            "stored_at": stored_at,
            "payload": base_payload,
        }
    return json.dumps(
        _apply_forecast_guess_note(_decorate_fresh(base_payload), raw, guessed)
    )


def _fallback_trend_payload(location_display: str) -> dict:
    """Disclosed mock-shaped payload when the archive fetch fails (D-03).

    Never raises: stale-marked zeros plus the fallback note, mirroring the
    current-tool outage contract. Window fields stay truthful (30-day window
    with empty dates) and both note plus advisory surface the literal
    fallback sentence so cached, stale, and fallback states disclose alike.
    Never stored as a fresh cache entry (T-08-05).
    """
    note_text = (
        f"{_FALLBACK_NOTE} Archive trend data unavailable for "
        f"{location_display}; showing fallback values (non-IMD model data)."
    )
    return {
        "location": location_display,
        "rain_sum_mm": 0.0,
        "temp_mean_c": 0.0,
        "temp_min_c": 0.0,
        "temp_max_c": 0.0,
        "wettest_day": "",
        "driest_day": "",
        "deviation_note": "Trend data unavailable; showing fallback values.",
        "window_days": 30,
        "window_start": "",
        "window_end": "",
        "source": "mock-climate-fallback (non-IMD model data)",
        "note": note_text,
        "advisory": note_text,
        "cached": False,
        "cache_age_s": 0,
        "stale": True,
    }


def _apply_trend_guess_note(payload: dict, raw: str, guessed: bool) -> dict:
    """Mirror the current-tool best-guess disclosure on trend payloads."""
    if guessed:
        note = (
            f"Showing best-guess data for {_FALLBACK_CITY.title()} "
            f"instead of {raw}."
        )
        payload["requested_location"] = raw
        payload["resolved_location"] = f"{_FALLBACK_CITY.title()} (best guess)"
        existing = str(payload.get("note", ""))
        payload["note"] = f"{note} {existing}".strip() if existing else note
        # Location always reflects the resolved city actually queried.
        payload["location"] = _FALLBACK_CITY.title()
    return payload


@tool("get_climate_trends")
def get_climate_trends(location: str) -> str:
    """Get the past-30-day climate trend for a location.

    Args:
        location: City, district, or 'lat,lon' string (e.g. 'Pune').

    Returns:
        A JSON string with 30-day rain sum, temp mean/min/max,
        wettest/driest days, a deviation note, the window dates, and the
        non-IMD source marker. Archive model data (non-IMD); a stamped
        mock fallback when the fetch fails.
    """
    settings = get_settings()
    _ = settings.WEATHER_API_KEY  # Reserved for the future IMD path; keyless live path.

    # Cap input at 120 chars before use (Phase 1 schema carryover).
    raw = ((location or "Unknown")[:_MAX_LOCATION_CHARS]).strip() or "Unknown"
    lookup_key = raw.lower()

    coords = CITY_COORDS.get(lookup_key)
    guessed = False
    if coords is not None:
        location_display = raw.title()
    else:
        parsed = _try_parse_latlon(raw)
        if parsed is not None:
            coords = parsed
            location_display = raw
        else:
            # Best-guess nearest-map anchor AND disclose the guess.
            # Never refuse and never substitute silently.
            coords = CITY_COORDS[_FALLBACK_CITY]
            guessed = True
            location_display = _FALLBACK_CITY.title()
    latitude, longitude = coords

    # D-03 cache discipline (Plan 02 hardening): tuple key namespaces trend
    # entries away from current plain-string keys and forecast tuple keys
    # so no collision is possible (T-08-05). Lock-guarded dict access.
    cache_key = ("climate", lookup_key)

    # Cache hit path: serve the unexpired entry with disclosure stamps.
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(cache_key)
    if entry is not None and now < entry["expires"]:
        age_s = int(now - entry["stored_at"])
        return json.dumps(
            _apply_trend_guess_note(_decorate_hit(entry["payload"], age_s), raw, guessed)
        )

    try:
        provider_data = imd_client.fetch_archive_open_meteo(latitude, longitude)
        mapped = imd_client.map_archive_to_payload(provider_data, location_display)
    except Exception:
        # Archive outage (D-03): exact parity with the current path.
        # Serve the expired entry stamped stale when one exists, else the
        # mock-shaped trend fallback. Neither branch is stored as a fresh
        # entry (T-08-05). Log full server-side; user payload stays
        # sanitized (no keys, URLs, or tracebacks).
        logger.exception("get_climate_trends archive fetch failed")
        with _CACHE_LOCK:
            stale_entry = _CACHE.get(cache_key)
        if stale_entry is not None:
            age_s = int(time.monotonic() - stale_entry["stored_at"])
            return json.dumps(
                _apply_trend_guess_note(
                    _decorate_stale(stale_entry["payload"], age_s), raw, guessed
                )
            )
        return json.dumps(
            _apply_trend_guess_note(_fallback_trend_payload(location_display), raw, guessed)
        )

    # Fresh success only: store the base payload (no disclosure stamps
    # stored), then return it stamped fresh. Fallbacks never reach this store.
    stored_at = time.monotonic()
    base_payload = dict(mapped)
    with _CACHE_LOCK:
        _CACHE[cache_key] = {
            "expires": stored_at + CACHE_TTL_S,
            "stored_at": stored_at,
            "payload": base_payload,
        }
    return json.dumps(_apply_trend_guess_note(_decorate_fresh(base_payload), raw, guessed))
