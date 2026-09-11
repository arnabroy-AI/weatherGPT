# Phase 2: IMD live data — API coverage matrix

**Phase:** 02-imd-live-data · **Date:** 2026-09-11
**Engine:** Open-Meteo keyless live path behind the IMD-shaped `get_current_weather` seam (D-09).
Phase 1 carryovers untouched: threadpool offload, 30s retry, stdlib logging, X-Request-ID, 502/500 error mapping.

## INTEGRATE

| Capability | Status | Scope note |
|------------|--------|------------|
| Current weather via Open-Meteo `forecast` `current` endpoint behind the IMD-shaped seam | Live | Live values mapped to the 14-key contract with non-IMD disclosure in `source`/advisory. |
| Day-wise forecast | INTEGRATE | Superseded by Phase 3 — see `.planning/phases/03-forecast-alerts/COVERAGE.md` (daily fetch behind the IMD-shaped seam, day-wise mapping, worst-day Alert line). |
| Past-30-day climate trends via Open-Meteo archive `daily` fetch behind the IMD-shaped seam | INTEGRATE | Phase 8 `get_climate_trends` requests `archive-api.open-meteo.com` with `past_days` 30 and daily `temperature_2m_max,temperature_2m_min,precipitation_sum` behind the `imd_client` seam; MockTransport plus fixtures only in CI, disclosed non-IMD. |

## OPT-OUT

| Capability | Status | Reason |
|------------|--------|--------|
| Alert color issuance | Derived heuristic only | Real IMD colors arrive on gateway cutover; derived levels never claimed as IMD-issued. |
| Geocoding at runtime | Frozen map | Frozen curated 18-city map per D-07, no runtime geocoding in CI. |
| Persistent or disk cache | Forbidden | Forbidden by D-03 (10-min in-memory TTL only). |
| Agent prompt or route or schema changes | Frozen | Frozen by DATA-03 and D-06 (tool seam only, LLM path fail-loud). |
