"""Tool contract test: frozen mock JSON shape for `get_current_weather`.

Covers the mock payload without touching `tools/weather.py`: invokes the
tool through its LangChain `invoke` entrypoint, parses the returned JSON
string, and asserts the frozen contract keys Phase 2 builds on.
"""

import json

from tools.weather import get_current_weather


def test_weather_tool_mock_contract():
    """Mock tool returns parseable JSON echoing Mumbai with contract keys."""
    raw = get_current_weather.invoke({"location": "Mumbai"})
    data = json.loads(raw)
    assert data["location"] == "Mumbai"
    assert "temperature_c" in data
    assert "alert_level" in data
    assert "source" in data


def test_weather_tool_name_frozen():
    """Tool name stays `get_current_weather` so Phase 2 keeps the signature."""
    assert get_current_weather.name == "get_current_weather"
