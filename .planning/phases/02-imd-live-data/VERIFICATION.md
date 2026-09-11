# Phase 2: IMD live data — Verification Report

**Phase goal:** Real IMD current weather with cache + fallback
**Verified:** 2026-09-11 (UTC)
**Status:** PASSED
**Score:** 3/3 success criteria verified (plus 6 guard checks)
**Method:** Goal-backward — ran `python -m pytest tests/ -q` myself plus an inline
Pune probe; read `tools/weather.py`, `tools/imd_client.py`, `tests/test_imd_client.py`,
`tests/test_weather_tool.py`, `tests/fixtures/open_meteo_mumbai.json`, `services/agent.py`.
SUMMARY.md claims were treated as leads, not evidence.

## Success criteria

### SC1 — "Current weather in Pune" returns real live-engine values with source cited ✅

**Evidence (my own run, MockTransport serving the recorded fixture):**

```json
{"location": "Pune", "observed_at_utc": "2026-09-10T19:30", "temperature_c": 26.1,
 "feels_like_c": 31.8, "humidity_pct": 90, "condition": "Overcast",
 "wind_kph": 4.0, "wind_direction": "NNW", "pressure_hpa": 1010.4,
 "visibility_km": 24.0,
 "source": "open-meteo-live (non-IMD model data; IMD-direct pending)",
 "alert_level": "Green",
 "advisory": "Overcast in Pune (non-IMD model data). No severe weather expected.",
 "cached": false, "cache_age_s": 0, "stale": false}
```

- Fixture values flow end-to-end: `temperature_c 26.1`, `NNW`, `Green` match the
  recorded Open-Meteo Mumbai sample (`tests/fixtures/open_meteo_mumbai.json`,
  `current.temperature_2m == 26.1`).
- `source` cites the engine and discloses non-authenticity per D-09.
- Suite tests covering this: `test_mapping`, `test_contract_unchanged`,
  `test_tracer_pune_fixture_path` — all passed in my run.
- Per CONTEXT D-09 (Open-Meteo fork, user-decided), "real IMD values" for this phase
  means live-engine values behind the IMD-shaped seam with disclosed non-authenticity —
  that is exactly what the payload shows. No claim of IMD issuance anywhere in payloads.

### SC2 — Simulated provider outage still returns a degraded answer in <5s ✅

- `test_outage_fallback` (MockTransport raising `httpx.ConnectError`): returns parseable
  JSON, `source == "mock-imd-fallback"`, all 14 frozen keys, advisory containing
  `live data unavailable`, deterministic placeholders (`temperature_c 29.5`,
  `condition "Light rain unavailable"`, `alert_level Yellow`), wall time asserted
  `< 5.0s` — passed in my run.
- `test_stale_on_error`: expired entry + dead transport serves stale data stamped
  `stale: true`, source suffixed `+stale-fallback`, fixture values (26.1) proving the
  expired entry was served — passed in my run.
- Fallback never pins the cache (post-fallback healthy invoke refetches) — asserted
  in-test, passed.

### SC3 — Repeated identical queries hit cache (no duplicate upstream calls within TTL) ✅

- `test_cache_hit`: two identical Pune invokes → exactly 1 transport hit; first
  `cached: false`/`cache_age_s: 0`, second `cached: true`/non-negative int — passed.
- `test_ttl_expiry`: pre-seeded expired entry forces refetch (1 hit, `cached: false`,
  live source) — passed.
- Implementation matches D-03: `CACHE_TTL_S = 600`, key `location.strip().lower()`,
  `threading.Lock`-guarded, fallback payloads never stored as fresh (read in
  `tools/weather.py:53-55, 179-218`).

## Guard checks

| Guard | Result |
|-------|--------|
| Tool contract frozen (`get_current_weather(location: str) -> JSON string`, 14 keys) | ✅ `tool("get_current_weather")`, JSON-string return; tests assert `FROZEN_KEYS <= keys`; `services/agent.py` untouched (still Phase 1 shape, imports the tool, no fetch logic duplicated) |
| No IMD-issued claims (D-09) | ✅ Only occurrences of "IMD-issued" are negative statements in comments/docstrings ("never described as IMD-issued"); every payload `source`/`advisory` says non-IMD model data/estimate |
| Secrets never leak | ✅ `test_no_key_leak` (`SECRET_PROBE_42` absent from JSON + logs) passed; `test_key_missing_live_path` (empty key → live path, D-02) passed; `test_secrets.py` + `test_error_contract.py` green in full suite |
| No forecasts (Phase 3) leaking in | ✅ Single tool only; no forecast/day-wise function exists; `hourly=precipitation` is solely the 24h-rain sum input (never `current.precipitation` — Pitfall 1 avoided, read at `imd_client.py:212-224`) |
| No live network in CI tests | ✅ No `api.open-meteo.com` / `api.imd.gov.in` references in `tests/`; all provider HTTP via `httpx.MockTransport`; full suite ran locally in ~8s with no network waits |
| City breadth + best-guess (D-07/D-08) | ✅ `CITY_COORDS` has exactly 18 entries incl. Nashik/Pune; `test_city_normalisation` (case/whitespace-insensitive, 1 hit) and `test_best_guess` (`Atlantis XYZ` → disclosed Mumbai guess) passed |

## Full-suite result (my run)

`python -m pytest tests/ -q` → **30 passed, 1 skipped** (skip = opt-in live
OpenRouter test, `WEATHERGPT_LIVE` unset — expected). Matches the 02-03-SUMMARY claim.

## Notes (non-blocking)

- `H:/weatherGPT/check_fallback_tmp.py` (961 bytes) is still on disk — the inert
  throwaway outage-drill script flagged in 02-01-SUMMARY §Leftover. Harmless
  (imports tools only, runs nothing on import) but should be deleted manually.
- Git commits for the phase are blocked by a stale `.git/index.lock` (environment
  issue, documented across all three SUMMARYs; repo has no commits yet). Code is
  verified on disk; commit when the lock clears. Not a goal gap.
- `COVERAGE.md` INTEGRATE/OPT-OUT matrix exists with one-line reasons per row ✅

## Verdict

All 3 success criteria hold in the codebase, proven by tests I executed myself plus
direct code reads. DATA-01, DATA-02, DATA-03 satisfied within the D-09 Open-Meteo
fork. No gaps.
