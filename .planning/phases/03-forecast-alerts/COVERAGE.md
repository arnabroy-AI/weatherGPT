# Phase 3: Forecast + alerts — API coverage matrix

**Phase:** 03-forecast-alerts · **Date:** 2026-09-11
**Engine:** Open-Meteo keyless daily fetch behind the IMD-shaped forecast seam (D-01).
Supersedes the Phase 2 OPT-OUT day-wise forecast row (see `.planning/phases/02-imd-live-data/COVERAGE.md`).

## INTEGRATE

| Capability | Status | Scope note |
|------------|--------|------------|
| Day-wise forecast via Open-Meteo `daily` fetch behind the IMD-shaped seam | Live | `fetch_forecast_open_meteo` requests `temperature_2m_max, temperature_2m_min, precipitation_probability_max, precipitation_sum, weathercode, wind_speed_10m_max`; keyless model data with non-IMD disclosure in `source`. |
| 5-day day-wise mapping with per-day alerts | Live | `map_forecast_to_payload` returns exactly N entries of date, temp_min_c, temp_max_c, rain_chance_pct, condition, alert_level; days clamped 3–5. |
| Worst-day `Alert:` line | Live | `Alert: <level> (<3-letter weekday>)` for the severest day in range (D-04); matches the Phase 1 `Alert: <level>` reply regex. |
| Per-day plus rollup advisories | Live | Per-day advisory text for each Orange/Red day plus one overall trip-level rollup line (D-05; Plan 02). |
| Location-plus-days 10-minute cache | Live | Shared in-memory `_CACHE` on the tuple key `("forecast", lookup_key, days)` with 600s TTL; never stores fallback/partial payloads (D-06). |
| Partial current-only fallback | Live | Forecast outage serves live current values with `forecast_days=[]`, `forecast_available=False`, and an honest "forecast unavailable" note; never synthesizes mock days (D-07). |
| Minimal agent wiring | Live | New tool registered on the agent plus one-line prompt rule for when to call it (D-08; Plan 02). |
| Past-30-day climate trends via Open-Meteo archive `daily` fetch behind the IMD-shaped seam | INTEGRATE | Phase 8 `get_climate_trends` requests `archive-api.open-meteo.com` with `past_days` 30 and daily `temperature_2m_max,temperature_2m_min,precipitation_sum` behind the `imd_client` seam; MockTransport plus fixtures only in CI, disclosed non-IMD. |

## OPT-OUT

| Capability | Status | Reason |
|------------|--------|--------|
| Persistent or disk cache | Forbidden | Forbidden by D-06 (10-min in-memory TTL only). |
| Full mock forecast bundles | Forbidden | Forbidden by D-07 (partial current-only fallback with honest note, never synthesized days). |
| Separate stricter alert thresholds | Rejected | Rejected by D-03 (reuse the existing `derive_alert_level` heuristic per forecast day). |
| Forecast orchestration | Deferred | Deferred to Phase 4 by D-08 (location resolution, agri/climate orchestration out of scope). |
