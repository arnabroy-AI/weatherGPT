"""Advisory + rollup + agent wiring tests (Phase 3, Plan 02).

All provider HTTP is fixture-shaped dicts fed directly to
``map_forecast_to_payload`` — no test touches the live network.
"""

import copy
import json
import re
from datetime import datetime
from pathlib import Path

from tools import imd_client
from services.agent import SYSTEM_PROMPT, _TOOLS, _derive_alert_level

FORECAST_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "open_meteo_forecast_mumbai.json"
)

ALERT_LINE_RE = re.compile(r"Alert: (Green|Yellow|Orange|Red) \([A-Za-z]{3}\)")


def _fixture() -> dict:
    return json.loads(FORECAST_FIXTURE_PATH.read_text(encoding="utf-8"))


def _calm_fixture() -> dict:
    """All-Green 5-day payload: clear skies, no rain, light wind."""
    fixture = _fixture()
    fixture["daily"] = dict(fixture["daily"])
    fixture["daily"]["weathercode"] = [1, 0, 2, 1, 0]
    fixture["daily"]["precipitation_sum"] = [0.0, 0.0, 0.0, 0.0, 0.0]
    fixture["daily"]["precipitation_probability_max"] = [5, 0, 10, 5, 0]
    fixture["daily"]["wind_speed_10m_max"] = [10.0, 8.0, 12.0, 9.0, 11.0]
    return fixture


def _red_fixture() -> dict:
    """Force day 0 to Red (code 99 + 120mm) while keeping an Orange day."""
    fixture = _fixture()
    fixture["daily"] = dict(fixture["daily"])
    codes = list(fixture["daily"]["weathercode"])
    rain = list(fixture["daily"]["precipitation_sum"])
    codes[0] = 99
    rain[0] = 120.0
    fixture["daily"]["weathercode"] = codes
    fixture["daily"]["precipitation_sum"] = rain
    return fixture


def test_orange_day_advisory_text():
    """Fixture Orange day advisory carries the vetted Orange guidance."""
    mapped = imd_client.map_forecast_to_payload(_fixture(), "Mumbai", 5)

    orange_days = [d for d in mapped["days"] if d["alert_level"] == "Orange"]
    assert orange_days, "fixture must contain an Orange day"
    for day in orange_days:
        assert "avoid unnecessary travel" in day["advisory"].lower()
        assert "non-imd" in day["advisory"].lower()


def test_red_day_advisory_text():
    """Red day advisory carries the vetted Red stay-indoors guidance."""
    mapped = imd_client.map_forecast_to_payload(_red_fixture(), "Mumbai", 5)

    red_days = [d for d in mapped["days"] if d["alert_level"] == "Red"]
    assert red_days, "mutated fixture must contain a Red day"
    for day in red_days:
        assert "avoid travel and stay indoors" in day["advisory"].lower()


def test_green_days_calm_wording():
    """Green days carry the no-severe wording, never Orange/Red guidance."""
    mapped = imd_client.map_forecast_to_payload(_calm_fixture(), "Mumbai", 5)

    assert mapped["worst_alert"] == "Green"
    for day in mapped["days"]:
        assert day["alert_level"] == "Green"
        assert "no severe weather expected" in day["advisory"].lower()


def test_rollup_severe_names_worst_level_weekday_dates():
    """Severe rollup names worst level + worst weekday + severe dates."""
    fixture = _fixture()
    mapped = imd_client.map_forecast_to_payload(fixture, "Mumbai", 5)
    rollup = mapped["rollup_advisory"]

    worst_weekday = datetime.fromisoformat(mapped["worst_day"]).strftime("%a")
    severe_dates = [
        d["date"] for d in mapped["days"] if d["alert_level"] in ("Orange", "Red")
    ]

    assert mapped["worst_alert"] in rollup
    assert worst_weekday in rollup
    assert mapped["worst_day"] in rollup
    for date in severe_dates:
        assert date in rollup
    assert "reconsider outdoor plans" in rollup.lower()
    assert "non-imd" in rollup.lower()


def test_rollup_calm_states_no_severe():
    """All-Green rollup states no severe weather expected with span."""
    mapped = imd_client.map_forecast_to_payload(_calm_fixture(), "Mumbai", 5)
    rollup = mapped["rollup_advisory"]

    assert "no severe weather expected" in rollup.lower()
    assert "Mumbai" in rollup
    assert mapped["days"][0]["date"] in rollup
    assert mapped["days"][-1]["date"] in rollup


def test_alert_line_unchanged_format():
    """alert_line keeps the Plan 01 worst-day format (D-04)."""
    mapped = imd_client.map_forecast_to_payload(_fixture(), "Mumbai", 5)

    assert ALERT_LINE_RE.search(mapped["alert_line"]), mapped["alert_line"]
    expected_tag = datetime.fromisoformat(mapped["worst_day"]).strftime("%a")
    assert mapped["alert_line"] == f"Alert: {mapped['worst_alert']} ({expected_tag})"


def test_agent_tools_registered():
    """Agent _TOOLS holds the weather tools (Phase 8 adds get_climate_trends)."""
    names = {getattr(t, "name", "") for t in _TOOLS}
    assert names == {"get_current_weather", "get_weather_forecast", "get_climate_trends"}


def test_agent_prompt_single_forecast_rule():
    """SYSTEM_PROMPT mentions get_weather_forecast exactly once."""
    assert SYSTEM_PROMPT.count("get_weather_forecast") == 1
    assert "multi-day" in SYSTEM_PROMPT.lower()


def test_worst_day_line_parses_orange():
    """Phase 1 regex still parses the Orange worst-day line."""
    assert _derive_alert_level("Trip outlook.\nAlert: Orange (Sat)") == "Orange"


def test_worst_day_line_parses_red():
    """Phase 1 regex still parses the Red worst-day variant."""
    assert _derive_alert_level("Trip outlook.\nAlert: Red (Mon)") == "Red"


def test_mapped_worst_day_line_parses():
    """The actual mapper alert_line parses back to its worst level."""
    mapped = imd_client.map_forecast_to_payload(_red_fixture(), "Mumbai", 5)
    assert _derive_alert_level(mapped["alert_line"]) == mapped["worst_alert"] == "Red"
    assert copy.deepcopy(mapped["days"])  # payload stays JSON-serializable
    json.dumps(mapped)
