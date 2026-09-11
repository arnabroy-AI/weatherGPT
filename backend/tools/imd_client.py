"""Open-Meteo live-data client behind the IMD-shaped tool seam.

Phase 2 (D-09): Open-Meteo is the keyless live engine; every payload this
module emits discloses non-authentic model data via its ``source`` string.
All provider knowledge (fetch, WMO/compass tables, alert derivation, field
mapping) lives here so the future IMD-direct cutover swaps one module and
``tools/weather.py`` keeps its frozen ``get_current_weather`` contract.

Threat notes (plan T-02-01..T-02-03):
- Provider JSON is parsed defensively (``.get`` + type checks, never eval);
  unmapped WMO codes yield ``"Unknown (code N)"``, never a crash.
- ``derive_alert_level`` is a conservative heuristic with a Green default;
  derived levels are never described as IMD-issued anywhere.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 6.0

CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation,weather_code,pressure_msl,wind_speed_10m,"
    "wind_direction_10m,visibility"
)

# Disclosure string stamped on every live-path payload (D-05/D-09).
LIVE_SOURCE = "open-meteo-live (non-IMD model data; IMD-direct pending)"

# Frozen WMO weather-code -> condition text. Code 3 is contract-pinned to
# "Overcast"; anything unmapped yields "Unknown (code N)", never a crash.
WMO_CONDITION: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

COMPASS_16: Tuple[str, ...] = (
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
)

# Module-level transport override for tests (httpx.MockTransport).
# Production path leaves this None so a real connection is used.
_TRANSPORT_OVERRIDE: Optional[httpx.BaseTransport] = None


def set_transport(transport: Optional[httpx.BaseTransport]) -> None:
    """Pin a transport (e.g. httpx.MockTransport) for tests; None restores live."""
    global _TRANSPORT_OVERRIDE
    _TRANSPORT_OVERRIDE = transport


def reset_transport() -> None:
    """Clear any test transport override."""
    set_transport(None)


def wmo_to_text(code: Any) -> str:
    """Map a WMO weather code to display text; unknown codes never crash."""
    try:
        n = int(code)
    except (TypeError, ValueError):
        return f"Unknown (code {code})"
    return WMO_CONDITION.get(n, f"Unknown (code {n})")


def degrees_to_compass(degrees: Any) -> str:
    """Convert wind degrees to 16-point compass; non-numeric input yields 'Unknown'."""
    try:
        deg = float(degrees)
    except (TypeError, ValueError):
        return "Unknown"
    index = int((deg + 11.25) / 22.5) % 16
    return COMPASS_16[index]


def derive_alert_level(
    weather_code: Any,
    wind_kph: Any = 0.0,
    rainfall_mm_24h: Any = 0.0,
) -> str:
    """Conservative severity heuristic over model data; defaults to Green.

    Severe thunderstorm codes (95/96/99), heavy rain (65) and violent
    showers (80-82) all map upward. This is estimation, never an
    IMD-issued warning.
    """
    try:
        code = int(weather_code)
    except (TypeError, ValueError):
        code = -1
    try:
        wind = float(wind_kph)
    except (TypeError, ValueError):
        wind = 0.0
    try:
        rain = float(rainfall_mm_24h)
    except (TypeError, ValueError):
        rain = 0.0

    if code in (96, 99) or wind >= 90.0 or rain >= 100.0:
        return "Red"
    if code in (95, 65, 82, 75, 86) or wind >= 60.0 or rain >= 50.0:
        return "Orange"
    if (
        code
        in (
            80, 81, 61, 63, 66, 67, 71, 73, 77, 85,
            51, 53, 55, 56, 57, 45, 48,
        )
        or wind >= 30.0
        or rain >= 20.0
    ):
        return "Yellow"
    return "Green"


def fetch_open_meteo(
    latitude: float,
    longitude: float,
    transport: Optional[httpx.BaseTransport] = None,
) -> Dict[str, Any]:
    """GET current + hourly-precipitation from Open-Meteo (sync, 6s timeout).

    Args:
        latitude: Station latitude in degrees.
        longitude: Station longitude in degrees.
        transport: Optional httpx transport; falls back to the module-level
            test override, else a live connection.

    Returns:
        Decoded provider JSON dict.

    Raises:
        RuntimeError: Sanitized fetch/parse failure (no URLs, keys, or
            tracebacks in the message; full detail goes to the log only).
    """
    active = transport if transport is not None else _TRANSPORT_OVERRIDE
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": CURRENT_FIELDS,
        "hourly": "precipitation",
        "past_days": 1,
        "wind_speed_unit": "kmh",
        "timezone": "UTC",
    }
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, transport=active) as client:
            response = client.get(OPEN_METEO_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # Log full, send safe (T-02-02).
        logger.exception("Open-Meteo fetch failed")
        raise RuntimeError("Live weather fetch failed; retry shortly.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    return data


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    # Guard against NaN/inf leaking into JSON consumers.
    if result != result or result in (float("inf"), float("-inf")):
        return default
    return result


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _rainfall_last_24h(data: Dict[str, Any], current: Dict[str, Any]) -> float:
    """Sum the last 24 hourly precipitation steps (never current.precipitation).

    Falls back to ``current.precipitation`` only when hourly data is absent,
    else 0.0. Missing rain must read as dry, never as an error.
    """
    hourly = data.get("hourly")
    if isinstance(hourly, dict):
        series = hourly.get("precipitation")
        if isinstance(series, list) and series:
            window: List[Any] = series[-24:]
            return round(sum(_as_float(v, 0.0) for v in window), 2)
    return round(_as_float(current.get("precipitation"), 0.0), 2)


def _build_advisory(alert_level: str, condition: str, location_display: str) -> str:
    """1-2 line safety text; Orange/Red carry do/avoid guidance (T-02-03)."""
    safe_location = str(location_display)[:80]
    safe_condition = str(condition)[:80]
    if alert_level == "Red":
        return (
            f"Severe weather ({safe_condition}) near {safe_location} "
            "(non-IMD model estimate). Avoid travel and stay indoors; "
            "move away from flood-prone areas."
        )
    if alert_level == "Orange":
        return (
            f"Rough weather ({safe_condition}) near {safe_location} "
            "(non-IMD model estimate). Avoid unnecessary travel; "
            "carry rain gear and stay alert."
        )
    if alert_level == "Yellow":
        return (
            f"{safe_condition} likely in {safe_location} "
            "(non-IMD model data). Carry an umbrella; no severe weather expected."
        )
    return (
        f"{safe_condition} in {safe_location} (non-IMD model data). "
        "No severe weather expected."
    )


def map_open_meteo_to_payload(
    data: Dict[str, Any], location_display: str
) -> Dict[str, Any]:
    """Map provider JSON to exactly the 14 frozen tool keys (T-02-01).

    Raises:
        RuntimeError: Sanitized message when the provider schema is unusable.
    """
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    current = data.get("current")
    if not isinstance(current, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")

    display = str(location_display or "Unknown")[:80] or "Unknown"
    code = _as_int(current.get("weather_code"), -1)
    condition = wmo_to_text(code)[:80]
    wind_kph = _as_float(current.get("wind_speed_10m"), 0.0)
    rainfall = _rainfall_last_24h(data, current)
    alert_level = derive_alert_level(code, wind_kph, rainfall)

    visibility_raw = current.get("visibility")
    visibility_km: Optional[float]
    if isinstance(visibility_raw, bool) or visibility_raw is None:
        visibility_km = None  # Absent visibility is None, never 0.0 (fog).
    else:
        try:
            visibility_km = round(float(visibility_raw) / 1000.0, 2)
        except (TypeError, ValueError):
            visibility_km = None

    observed = current.get("time")
    if not isinstance(observed, str) or not observed:
        from datetime import datetime, timezone

        observed = datetime.now(timezone.utc).isoformat()

    return {
        "location": display,
        "observed_at_utc": observed,
        "temperature_c": _as_float(current.get("temperature_2m"), 0.0),
        "feels_like_c": _as_float(current.get("apparent_temperature"), 0.0),
        "humidity_pct": _as_int(current.get("relative_humidity_2m"), 0),
        "condition": condition,
        "rainfall_mm_last_24h": rainfall,
        "wind_kph": wind_kph,
        "wind_direction": degrees_to_compass(current.get("wind_direction_10m")),
        "pressure_hpa": _as_float(current.get("pressure_msl"), 0.0),
        "visibility_km": visibility_km,
        "source": LIVE_SOURCE,
        "alert_level": alert_level,
        "advisory": _build_advisory(alert_level, condition, display),
    }


# Daily fields requested for the 5-day forecast path (Phase 3, D-01/D-02).
FORECAST_DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,precipitation_sum,"
    "weathercode,wind_speed_10m_max"
)

# Severity ordering for the worst-day rollup (D-04); Green < Yellow < Orange < Red.
_ALERT_SEVERITY = {"Green": 0, "Yellow": 1, "Orange": 2, "Red": 3}


def fetch_forecast_open_meteo(
    latitude: float,
    longitude: float,
    days: int = 5,
    transport: Optional[httpx.BaseTransport] = None,
) -> Dict[str, Any]:
    """GET daily forecast aggregates from Open-Meteo (sync, 6s timeout).

    Args:
        latitude: Station latitude in degrees.
        longitude: Station longitude in degrees.
        days: Day count requested (upstream forecast_days).
        transport: Optional httpx transport; falls back to the module-level
            test override, else a live connection.

    Returns:
        Decoded provider JSON dict with a ``daily`` section.

    Raises:
        RuntimeError: Sanitized fetch/parse failure (no URLs, keys, or
            tracebacks in the message; full detail goes to the log only).
    """
    try:
        day_count = int(days)
    except (TypeError, ValueError):
        day_count = 5
    if day_count < 1 or day_count > 16:
        day_count = 5
    active = transport if transport is not None else _TRANSPORT_OVERRIDE
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": FORECAST_DAILY_FIELDS,
        "forecast_days": day_count,
        "wind_speed_unit": "kmh",
        "timezone": "UTC",
    }
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, transport=active) as client:
            response = client.get(OPEN_METEO_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # Log full, send safe (T-03-02).
        logger.exception("Open-Meteo forecast fetch failed")
        raise RuntimeError("Live weather fetch failed; retry shortly.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    return data


def _daily_list(daily: Dict[str, Any], *names: str) -> List[Any]:
    """Return the first list found under any of the candidate daily keys."""
    for name in names:
        values = daily.get(name)
        if isinstance(values, list):
            return values
    return []


def _weekday_tag(date_str: Any) -> str:
    """Three-letter weekday (e.g. Sat) for an ISO date; never raises."""
    from datetime import datetime

    try:
        text = str(date_str)
        return datetime.fromisoformat(text).strftime("%a")
    except (TypeError, ValueError):
        return "N/A"


def map_forecast_to_payload(
    data: Dict[str, Any], location_display: str, days: int = 5
) -> Dict[str, Any]:
    """Map provider daily JSON to the forecast payload (T-03-01).

    Each day entry holds date, temp_min_c, temp_max_c, rain_chance_pct,
    condition (via ``wmo_to_text``), and alert_level (via
    ``derive_alert_level``). ``worst_alert`` is the severest per-day level
    and ``alert_line`` is ``"Alert: <level> (<weekday>)"`` per D-04, which
    still matches the Phase 1 ``Alert: <level>`` reply regex.

    Short or missing daily arrays degrade to safe defaults; a wholly
    unusable schema raises a sanitized RuntimeError. Derived levels are
    never described as IMD-issued.
    """
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")

    try:
        day_count = int(days)
    except (TypeError, ValueError):
        day_count = 5
    if day_count < 1 or day_count > 16:
        day_count = 5

    display = str(location_display or "Unknown")[:80] or "Unknown"

    times = _daily_list(daily, "time")
    tmax = _daily_list(daily, "temperature_2m_max")
    tmin = _daily_list(daily, "temperature_2m_min")
    rain_chance = _daily_list(daily, "precipitation_probability_max")
    rain_sum = _daily_list(daily, "precipitation_sum")
    codes = _daily_list(daily, "weathercode", "weather_code")
    winds = _daily_list(daily, "wind_speed_10m_max")

    day_entries: List[Dict[str, Any]] = []
    for index in range(day_count):
        raw_date = times[index] if index < len(times) else ""
        date_str = str(raw_date)[:10] if isinstance(raw_date, str) and raw_date else ""
        hi = _as_float(tmax[index], 0.0) if index < len(tmax) else 0.0
        lo = _as_float(tmin[index], 0.0) if index < len(tmin) else 0.0
        chance_raw = _as_int(rain_chance[index], 0) if index < len(rain_chance) else 0
        chance = max(0, min(100, chance_raw))
        code = _as_int(codes[index], -1) if index < len(codes) else -1
        wind = _as_float(winds[index], 0.0) if index < len(winds) else 0.0
        precip = _as_float(rain_sum[index], 0.0) if index < len(rain_sum) else 0.0
        condition = wmo_to_text(code)[:80]
        level = derive_alert_level(code, wind, precip)
        day_label = f"{display} on {date_str}" if date_str else display
        day_entries.append(
            {
                "date": date_str,
                "temp_min_c": lo,
                "temp_max_c": hi,
                "rain_chance_pct": chance,
                "condition": condition,
                "alert_level": level,
                "advisory": _build_advisory(level, condition, day_label),
            }
        )

    worst_alert = "Green"
    worst_day = day_entries[0]["date"] if day_entries else ""
    for entry in day_entries:
        if _ALERT_SEVERITY.get(entry["alert_level"], 0) > _ALERT_SEVERITY.get(
            worst_alert, 0
        ):
            worst_alert = entry["alert_level"]
            worst_day = entry["date"]
    alert_line = f"Alert: {worst_alert} ({_weekday_tag(worst_day)})"

    # D-05 rollup: one trip-level line reusing vetted advisory wording
    # authority (never IMD-issued). Calm spans name the location + day span;
    # severe spans name worst level + worst weekday + severe dates + guidance.
    present_dates = [entry["date"] for entry in day_entries if entry["date"]]
    if len(present_dates) >= 2:
        day_span = f"{present_dates[0]} to {present_dates[-1]}"
    elif present_dates:
        day_span = present_dates[0]
    else:
        day_span = "N/A"
    severe_dates = [
        entry["date"] or _weekday_tag(entry["date"])
        for entry in day_entries
        if entry["alert_level"] in ("Orange", "Red")
    ]
    if severe_dates:
        worst_weekday = _weekday_tag(worst_day)
        rollup_advisory = (
            f"{worst_alert} conditions worst on {worst_weekday} ({worst_day}) "
            f"near {display} (non-IMD model estimate). "
            f"Orange/Red on {', '.join(severe_dates)}; "
            "reconsider outdoor plans on those days."
        )
    else:
        rollup_advisory = (
            f"No severe weather expected in {display} from {day_span} "
            "(non-IMD model data)."
        )

    return {
        "location": display,
        "source": LIVE_SOURCE,
        "days": day_entries,
        "forecast_days": day_entries,
        "worst_alert": worst_alert,
        "worst_day": worst_day,
        "alert_line": alert_line,
        "rollup_advisory": rollup_advisory,
    }


# Phase 8 (D-01): archive endpoint + daily fields for the 30-day trend path.
OPEN_METEO_ARCHIVE_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
ARCHIVE_DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum"

# Disclosure string stamped on every archive-path payload (D-03).
ARCHIVE_SOURCE = "open-meteo-archive (non-IMD model data; IMD-direct pending)"


def fetch_archive_open_meteo(
    latitude: float,
    longitude: float,
    transport: Optional[httpx.BaseTransport] = None,
) -> Dict[str, Any]:
    """GET past-30-day daily aggregates from the Open-Meteo archive API.

    Mirrors :func:`fetch_open_meteo` (sync ``httpx.Client``, 6s timeout).
    Daily-only request, so no ``wind_speed_unit`` is sent.

    Args:
        latitude: Station latitude in degrees.
        longitude: Station longitude in degrees.
        transport: Optional httpx transport; falls back to the module-level
            test override, else a live connection.

    Returns:
        Decoded provider JSON dict with a ``daily`` section.

    Raises:
        RuntimeError: Sanitized fetch/parse failure (no URLs, keys, or
            tracebacks in the message; full detail goes to the log only).
    """
    active = transport if transport is not None else _TRANSPORT_OVERRIDE
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": 30,
        "daily": ARCHIVE_DAILY_FIELDS,
        "timezone": "UTC",
    }
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, transport=active) as client:
            response = client.get(OPEN_METEO_ARCHIVE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # Log full, send safe (T-08-02).
        logger.exception("Open-Meteo archive fetch failed")
        raise RuntimeError("Live weather fetch failed; retry shortly.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    return data


def map_archive_to_payload(
    data: Dict[str, Any], location_display: str
) -> Dict[str, Any]:
    """Map archive daily JSON to the 30-day trend payload (T-08-01).

    Computes ``rain_sum_mm`` (rounded 2dp sum of ``precipitation_sum``),
    ``temp_mean_c`` (rounded 2dp mean of per-day ``(max+min)/2``),
    ``temp_min_c``/``temp_max_c``, ``wettest_day``/``driest_day`` (strict
    argmax/argmin over the provider arrays, never invented), a one-sentence
    ``deviation_note`` comparing wettest-day rain against the window daily
    mean, plus ``window_days``/``window_start``/``window_end`` and the
    non-IMD ``source`` marker.

    Short arrays map over the available days only; a wholly missing
    ``daily`` section (or no usable day at all) raises a sanitized
    RuntimeError. NaN/inf values are guarded via :func:`_as_float`.
    """
    if not isinstance(data, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")
    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise RuntimeError("Live weather fetch failed; retry shortly.")

    display = str(location_display or "Unknown")[:80] or "Unknown"

    times = _daily_list(daily, "time")
    tmax = _daily_list(daily, "temperature_2m_max")
    tmin = _daily_list(daily, "temperature_2m_min")
    precip = _daily_list(daily, "precipitation_sum")

    day_count = max(len(times), len(tmax), len(tmin), len(precip))
    if day_count == 0:
        raise RuntimeError("Live weather fetch failed; retry shortly.")

    dates: List[str] = []
    highs: List[float] = []
    lows: List[float] = []
    rains: List[float] = []
    for index in range(day_count):
        raw_date = times[index] if index < len(times) else ""
        dates.append(
            str(raw_date)[:10] if isinstance(raw_date, str) and raw_date else ""
        )
        highs.append(_as_float(tmax[index], 0.0) if index < len(tmax) else 0.0)
        lows.append(_as_float(tmin[index], 0.0) if index < len(tmin) else 0.0)
        rains.append(_as_float(precip[index], 0.0) if index < len(precip) else 0.0)

    rain_sum = round(sum(rains), 2)
    daily_means = [(hi + lo) / 2.0 for hi, lo in zip(highs, lows)]
    temp_mean = round(sum(daily_means) / len(daily_means), 2) if daily_means else 0.0
    temp_min = round(min(lows), 2) if lows else 0.0
    temp_max = round(max(highs), 2) if highs else 0.0

    wettest_idx = max(range(len(rains)), key=lambda i: rains[i])
    driest_idx = min(range(len(rains)), key=lambda i: rains[i])
    wettest_day = dates[wettest_idx]
    driest_day = dates[driest_idx]
    wettest_rain = round(rains[wettest_idx], 2)
    daily_mean_rain = round(rain_sum / len(rains), 2) if rains else 0.0
    deviation_note = (
        f"Wettest day {wettest_day} at {wettest_rain} mm vs "
        f"window daily mean {daily_mean_rain} mm."
    )

    present_dates = [entry for entry in dates if entry]
    window_start = present_dates[0] if present_dates else ""
    window_end = present_dates[-1] if present_dates else ""

    return {
        "location": display,
        "rain_sum_mm": rain_sum,
        "temp_mean_c": temp_mean,
        "temp_min_c": temp_min,
        "temp_max_c": temp_max,
        "wettest_day": wettest_day,
        "driest_day": driest_day,
        "deviation_note": deviation_note,
        "window_days": day_count,
        "window_start": window_start,
        "window_end": window_end,
        "source": ARCHIVE_SOURCE,
    }
