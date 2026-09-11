import json

import httpx

from tools import imd_client
from tools.weather import get_current_weather


def down(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("simulated outage")


imd_client.set_transport(httpx.MockTransport(down))
try:
    d = json.loads(get_current_weather.invoke({"location": "Mumbai"}))
finally:
    imd_client.reset_transport()

print(sorted(d.keys()))
print(d["location"], "|", d["source"], "|", d["alert_level"])
blob = json.dumps(d)
assert len(d) == 14, d.keys()
assert "IMD-issued" not in blob
assert "WEATHER_API_KEY" not in blob
print("fallback OK")

# Unknown-code + unknown-city guards
assert imd_client.wmo_to_text(999) == "Unknown (code 999)"
assert imd_client.degrees_to_compass(342) == "NNW"
assert imd_client.derive_alert_level(3, 4.0, 0.0) == "Green"
assert imd_client.derive_alert_level(95, 4.0, 0.0) == "Orange"
assert imd_client.derive_alert_level(99, 4.0, 0.0) == "Red"
print("unit guards OK")
