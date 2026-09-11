# Phase 03 Plan 01: Daily Forecast Tracer Summary

**Status:** complete — all 3 tasks done, `tests/test_forecast.py` 8/8 green, full suite 38 passed + 1 skipped (pre-existing skip), zero regressions.

## What was built

End-to-end 5-day forecast slice for one known city through a new tool, fixture-backed, including the worst-day Alert line. `get_current_weather` left byte-identical; no `agent.py` changes (wiring is 03-02).

- `tools/imd_client.py` — added `fetch_forecast_open_meteo(latitude, longitude, days=5, transport=None)` requesting daily `temperature_2m_max, temperature_2m_min, precipitation_probability_max, precipitation_sum, weathercode, wind_speed_10m_max` with `wind_speed_unit=kmh`, `timezone=UTC`, reusing the transport override, `REQUEST_TIMEOUT_SECONDS`, and the sanitized RuntimeError pattern. Added `map_forecast_to_payload(provider_dict, location_display, days=5)` returning `location` (80-char cap), `source` (`LIVE_SOURCE` disclosure), `days`/`forecast_days` (exactly N entries of date, temp_min_c, temp_max_c, rain_chance_pct 0–100, condition via `wmo_to_text`, alert_level via `derive_alert_level`), `worst_alert` (Green<Yellow<Orange<Red, first-severest wins), `worst_day`, and `alert_line` (`Alert: <level> (<3-letter weekday>)`, matches the Phase 1 `Alert: <level>` reply regex). Defensive `.get` + type checks, safe defaults on short/missing arrays, sanitized RuntimeError only on wholly unusable schema. Existing `fetch_open_meteo`, `map_open_meteo_to_payload`, `WMO_CONDITION`, `derive_alert_level`, `_build_advisory` bodies untouched — pure append.
- `tools/weather.py` — new `get_weather_forecast(location, days=5)` langchain tool: same 120-char cap, `CITY_COORDS`/lat-lon parse/Mumbai best-guess + disclosure as the current tool; days clamped 3–5; location-plus-days cache on the shared `_CACHE` with 600s TTL, hit/stale stamps, stale-only-on-error; outage → partial payload (live current-weather values via the existing current fetch+map, `forecast_days=[]`, `forecast_available=False`, note containing `forecast unavailable for <location>`), never synthesizing mock days; only successful forecasts stored. `get_current_weather` byte-identical (verified: single `def`, nested `_apply_guess_note` intact, all Phase 1/2 suites green).
- `tests/fixtures/open_meteo_forecast_mumbai.json` — recorded-shape daily response, 2026-09-12…16, with a severe day (09-15, code 95, 78.5mm → Orange) so worst-day is Orange.
- `tests/test_forecast.py` — 8 tests, MockTransport only: mapping shape, worst-day line + weekday tag, unknown-code fallback, end-to-end Mumbai invoke, 1-hit cache proof, outage partial + no-cache-of-partial, days clamp (incl. upstream `forecast_days` param), forecast/current cache isolation.

## Verification evidence

- `python -m pytest tests/test_forecast.py -q` → **8 passed** (2.57s)
- `python -m pytest tests/ -q` → **38 passed, 1 skipped** (7.27s; skip is pre-existing). Baseline before changes was 30 passed + 1 skipped → +8 new, zero regressions.
- Spot-check: `Alert: Orange (Mon)` for the fixture (worst day 2026-09-15, a Monday) — matches `Alert: (Green|Yellow|Orange|Red) ([A-Za-z]{3})`.

## Deviations from plan

1. **Cache-key form (minor, stronger than spec):** plan said key as "normalised location plus pipe plus day count"; implemented as tuple `("forecast", lookup_key, days)` on the shared `_CACHE`. Rationale: a pipe-joined string key can theoretically collide with the current tool's plain-string key for adversarial input containing `|` (e.g. location `mumbai|5`); the tuple type can never equal a string key, so T-03-03 isolation is structural, not conventional. Same TTL, stamps, and stale semantics as specified.
2. **Mapper returns both `days` and `forecast_days` aliases** (same list) since the plan names the mapper output "a days list" while the tool contract requires `forecast_days` — avoids a translation layer and both names are asserted in tests.
3. **Mapper tolerates both `weathercode` and `weather_code` daily keys** (Open-Meteo uses both spellings across docs/versions); fixture uses `weathercode` per plan.

## Git commits (BEST-EFFORT — blocked, noted per instructions)

No commit was possible: the repo has no commits yet and a stale 0-byte `.git/index.lock` (dated 2026-09-11 12:23 AM) blocks even `git add` (`fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists`). Per environment notes I did not block on this and did not mutate `.git` internals. Files changed (uncommitted, verified present on disk): `tools/imd_client.py`, `tools/weather.py`, `tests/fixtures/open_meteo_forecast_mumbai.json` (new), `tests/test_forecast.py` (new).

## Known stubs / threat flags

None. No `TODO`/`placeholder`/empty-value stubs introduced; no new network endpoints, auth paths, or dependencies (httpx + pytest only, per T-03-SC). All three STRIDE mitigations (T-03-01 defensive daily parsing, T-03-02 sanitized errors, T-03-03 cache-key + never-store-partial) are implemented as specified.

## DoD mapping

- Mumbai 5-day forecast with min/max + rain chance × 5: ✅ (`test_end_to_end_forecast_mumbai`)
- Heavy-rain fixture day Orange in Alert line + `worst_alert`: ✅ (`test_mapping_worst_day_line`)
- Outage → partial current-only with honest note: ✅ (`test_outage_partial`)
- `get_current_weather` untouched: ✅ (append-only edits, full Phase 1/2 suite green)

## Self-Check: PASSED

- `tools/imd_client.py` fetch + mapping present; `tools/weather.py` new tool present, current tool single-def intact; fixture + 8-test file present on disk.
- No commits to verify (commit blocked by stale lock — documented above, not a code gap).
