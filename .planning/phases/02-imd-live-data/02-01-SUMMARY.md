# Phase 02 Plan 01: Tracer — Open-Meteo live path end-to-end — Summary

**Phase:** 02-imd-live-data · **Plan:** 01 · **Type:** tracer · **Date:** 2026-09-11
**Status:** complete (code + tests green; git commit blocked by stale lock — see § Commits)

## One-liner

Live current weather for known cities flows through a new `tools/imd_client.py`
Open-Meteo seam into the frozen `get_current_weather` JSON contract, verified by
fixture-grounded MockTransport tests (temperature_c 26.1, NNW, Green, open-meteo source).

## What was built

- **`tools/imd_client.py` (new)** — owns all provider knowledge:
  - `fetch_open_meteo(lat, lon, transport=None)` — sync `httpx.Client`, 6.0s
    timeout, GET `https://api.open-meteo.com/v1/forecast` with `current` set to
    temperature_2m, relative_humidity_2m, apparent_temperature, precipitation,
    weather_code, pressure_msl, wind_speed_10m, wind_direction_10m, visibility
    plus `hourly=precipitation`, `past_days=1`, `wind_speed_unit=kmh`,
    `timezone=UTC`. Injectable transport + module-level override
    (`set_transport`/`reset_transport`) for MockTransport tests.
  - Frozen WMO dict (code 3 → Overcast; unmapped → `Unknown (code N)`, never crash).
  - 16-point compass via `int((deg+11.25)/22.5)%16`.
  - `derive_alert_level()` — conservative: 96/99 → Red; 95/65/82 (+75/86) →
    Orange; 80/81 + rain/drizzle/fog/snow codes → Yellow; default Green.
  - `map_open_meteo_to_payload()` — emits exactly the 14 frozen keys; 24h rain
    summed from last 24 hourly steps (never `current.precipitation`); missing
    visibility → None (never 0.0); defensive `.get` + type checks throughout.
- **`tools/weather.py` (body only)** — normalises (`strip`, lower-lookup,
  title-case echo), resolves Mumbai (19.07283, 72.88261) and Pune (18.5204,
  73.8567), calls fetch + mapper, stamps
  `open-meteo-live (non-IMD model data; IMD-direct pending)`. Tool name,
  signature, JSON-string return unchanged. `WEATHER_API_KEY` read-and-ignored
  (D-02). Untouched: services/agent.py, api/routes.py, schemas/chat.py,
  main.py, core/config.py. No forecasts.
- **`tests/fixtures/open_meteo_mumbai.json` (new)** — recorded Mumbai sample
  per RESEARCH.md (current.temperature_2m 26.1, code 3, 342°, 1010.4 hPa,
  2026-09-10T19:30) extended with `visibility: 24000.0` and 48 hourly
  precipitation steps (all 0.0 → rainfall 0.0mm) so the mapper's hourly path
  is exercised deterministically.
- **`tests/test_imd_client.py` (new)** — `test_fixture_parses…`,
  `test_mapping` (14 keys + Mumbai values), `test_contract_unchanged`
  (location echo + frozen tool name), `test_tracer_pune_fixture_path`
  (Pune → 26.1/NNW/open-meteo/Green). All under MockTransport with
  set/reset fixture isolation.

## Deviations from Plan

### Auto-fixed / added (Rule 2 — required for acceptance criteria to hold)

**1. [Rule 2] Minimal disclosed fallback inside `tools/weather.py`**
- **Found during:** Task 1 — acceptance requires existing
  `tests/test_weather_tool.py` to pass unchanged AND the suite to pass with
  network disabled, but that test invokes the tool with no mock transport.
- **Fix:** on any fetch/map exception, return the deterministic mock-shaped
  payload stamped `mock-imd-fallback (non-IMD model data; live fetch
  unavailable)` (all 14 keys); full traceback to server log only, sanitized
  user payload (T-02-02, D-04/D-05).
- **Commit:** blocked (see § Commits).

No Rule 1 bugs, no Rule 3 blockers, no Rule 4 architecture questions. No new
packages (httpx + pytest already vendored) — no legitimacy gate triggered.

## Verification evidence

- `python -m pytest tests/test_imd_client.py tests/test_weather_tool.py -x -q` → **6 passed**
- `python -m pytest tests/ -q` → **22 passed, 1 skipped** (skip = opt-in live
  OpenRouter test, `WEATHERGPT_LIVE` unset — expected)
- Outage drill (MockTransport raising `httpx.ConnectError`): tool returns
  14-key fallback JSON, source `mock-imd-fallback`, no `IMD-issued` phrase, no
  key/URL/traceback leakage; unit guards pass (unknown code 999 →
  `Unknown (code 999)`; 342° → NNW; codes 3/95/99 → Green/Orange/Red).
- Threat check: T-02-01 (defensive parse + unknown-code string), T-02-02
  (log-full/send-safe), T-02-03 (conservative thresholds, Green default,
  `source` discloses non-IMD, phrase `IMD-issued` appears nowhere in code or
  payloads — verified by assertion).

## Known stubs / deferred

- None in this slice. Cache/TTL/outage/key-missing tests belong to later
  Phase 2 plans per the plan. Curated city map is intentionally minimal
  (Mumbai + Pune); unknown cities take the disclosed nearest-map guess (D-08)
  pending the full city-map plan.

## Leftover stray file (environment-blocked cleanup)

- `H:/weatherGPT/check_fallback_tmp.py` — throwaway outage-drill script.
  Deletion attempted 3× (PowerShell `Remove-Item -Force`, `python os.remove`);
  all fail with `Access denied` although ACLs grant write (external file lock
  in this environment). It is inert (imports tools only, runs nothing on
  import) — please delete manually. It was NOT staged for commit.

## Commits

- **Blocked, best-effort attempted:** `git add` + `git commit` of the four
  plan files fails with `fatal: Unable to create
  'H:/weatherGPT/.git/index.lock': File exists` (exit 128). No git process is
  running; the lock is stale but itself cannot be removed (`Access denied` on
  `.git/index.lock`). Repo additionally has no commits yet (fresh `main`).
  All four files are complete on disk and verified by the pytest runs above;
  commit when the lock clears:
  `git add tools/imd_client.py tools/weather.py
  tests/fixtures/open_meteo_mumbai.json tests/test_imd_client.py`

## Self-check

- [x] `tools/imd_client.py` imports cleanly (suite imports it in every test)
- [x] Fixture parses; `current.temperature_2m == 26.1`
- [x] Pune fixture path → temperature_c 26.1, NNW, open-meteo source, Green
- [x] Full suite green (22 passed, 1 expected skip)
- [ ] Commits exist — **FAILED (environment)**, documented above; no code
  impact, files verified on disk
