# Phase 02 Plan 03: Curated city map + best-guess disclosure, secret-safety, COVERAGE.md — Summary

**Phase:** 02-imd-live-data · **Plan:** 03 · **Type:** execute · **Date:** 2026-09-11
**Status:** complete (code + tests green; git commit blocked by stale lock — see § Commits)
**Requirements:** DATA-01, DATA-03

## One-liner

18 major Indian cities resolve case-insensitively through a frozen in-code map, unknown
locations return disclosed Mumbai best-guess data (requested/resolved/advisory fields), empty
keys still serve the live keyless path with zero secret leakage, and COVERAGE.md records the
INTEGRATE vs OPT-OUT matrix — full suite 30 passed + 1 expected skip with coverage report green.

## What was built

- **`tools/weather.py`** (body only; tool name/signature/14 frozen keys/source strings/cache-fallback untouched)
  - `CITY_COORDS` expanded from 2 to exactly 18 entries with plan-pinned lat-lon:
    Mumbai, Delhi, Pune, Nashik, Chennai, Kolkata, Bengaluru, Hyderabad, Ahmedabad,
    Jaipur, Lucknow, Bhopal, Patna, Thiruvananthapuram, Kochi, Guwahati, Chandigarh, Srinagar.
  - Lookup key `location.strip().lower()`; input capped at 120 chars before use
    (`_MAX_LOCATION_CHARS`, Phase 1 schema carryover).
  - Valid `lat,lon` strings parsing to two in-range floats (lat −90..90, lon −180..180)
    via `_try_parse_latlon` use the given coords directly (no guess); anything else
    unmappable (empty after strip, unknown name, unparsable/out-of-range lat-lon) falls
    back to Mumbai 19.07283,72.88261 with three disclosure fields: `requested_location`
    echoing raw input, `resolved_location` = `Mumbai (best guess)`, `advisory` prefixed
    with the literal `Showing best-guess data for Mumbai instead of X.` — never refuses,
    never substitutes silently. `location` reflects the resolved city (Mumbai) on the guess path.
  - Guess disclosure applied per-return via `_apply_guess_note`, so cache hits, fresh
    fetches, stale-serve, and generic fallback all carry it; base cached payloads stay
    stamp-free as before.
- **`tests/test_imd_client.py`** — 4 new tests (MockTransport, no live network):
  - `test_city_normalisation` — 18-entry map incl. Nashik/Pune; `MUMBAI` + surrounding
    whitespace and `mumbai` share one cache entry (exactly 1 transport hit), both return
    `location Mumbai` on the live source.
  - `test_best_guess` — `Atlantis XYZ` returns `resolved_location Mumbai (best guess)`,
    `requested_location Atlantis XYZ`, advisory starting with the literal
    `Showing best-guess data for Mumbai instead of Atlantis XYZ.` and containing `best-guess`.
  - `test_key_missing_live_path` — `WEATHER_API_KEY=""` still returns `open-meteo` source (D-02).
  - `test_no_key_leak` — `WEATHER_API_KEY=SECRET_PROBE_42` + dead transport: fallback JSON
    string and captured logs contain no `SECRET_PROBE_42` (sanitize_detail mirror).
- **`.planning/phases/02-imd-live-data/COVERAGE.md`** (new) — capability matrix with exactly
  two sections: INTEGRATE (current weather via Open-Meteo forecast `current` endpoint behind
  the IMD-shaped seam; live values mapped to the 14-key contract) and OPT-OUT (day-wise
  forecast → Phase 3; alert colors → derived heuristic only until gateway cutover; runtime
  geocoding → frozen map per D-07; disk cache → forbidden by D-03; agent/route/schema
  changes → frozen by DATA-03/D-06). Phase 1 carryovers confirmed untouched (threadpool,
  30s retry, logging, request-id, error mapping — none of those files modified).

## Deviations from Plan

None — plan executed exactly as written. Two conforming implementation choices within plan
discretion (not deviations):

1. **Guess-path `location` set to the resolved city (Mumbai).** The prior body echoed the
   unknown name while querying Mumbai coords (location/coords mismatch); the disclosure
   contract is cleaner when `location` reflects the city actually queried, with the raw
   input preserved in `requested_location`. All 14 frozen keys remain a subset of every
   payload (`FROZEN_KEYS <= set(...)` holds).
2. **Valid `lat,lon` passthrough.** The threat register (T-02-07) requires lat-lon parse
   validation, so well-formed in-range pairs are honored directly; only failed parses fall
   to the disclosed Mumbai guess — invalid input never becomes attacker-chosen coordinates.

No new packages (stdlib only) — no legitimacy gate triggered.

## Verification evidence

- `python -m pytest tests/test_imd_client.py -q` → **12 passed** (8 prior + 4 new)
- `python -m pytest tests/ -q` → **30 passed, 1 skipped** (skip = opt-in live OpenRouter
  test, `WEATHERGPT_LIVE` unset — expected; suite was 26 + 1 skipped before, +4 new = 30)
- Coverage gate (`COVERAGE_FILE` redirected to temp because a stale locked
  `.coverage.Arnab22.pid16508.X8Hc2Sbx` blocks the default erase — environment issue, see below):
  `python -m pytest tests/ -q --cov=. --cov-report=term-missing` → **30 passed, 1 skipped,
  TOTAL 86%**, `tests/test_imd_client.py 100%`, `tools/weather.py 90%`, `tools/imd_client.py 75%`.
- Threat check: T-02-07 (normalised lookup, validated lat-lon, disclosed Mumbai fallback),
  T-02-08 (key read-and-ignored; `SECRET_PROBE_42` absent from JSON + logs), T-02-09
  (requested + resolved + best-guess advisory end-to-end).

## Known stubs / deferred

- None in this slice. Forecasts remain Phase 3; IMD-direct cutover awaits portal
  registration (parallel human track); agent prompt/wiring stays Phase 4.

## Commits

- **Blocked, best-effort attempted:** `git add tools/weather.py tests/test_imd_client.py`
  fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists`
  (stale lock, same as Plans 01–02; repo still has no commits). All three plan files are
  complete on disk and verified by the pytest runs above; commit when the lock clears:
  `git add tools/weather.py tests/test_imd_client.py .planning/phases/02-imd-live-data/COVERAGE.md`

## Self-Check

- [x] Map has exactly 18 entries including Nashik and Pune
- [x] `MUMBAI` with trailing space → `location Mumbai` from the map path (1 transport hit)
- [x] `Atlantis XYZ` → `resolved_location Mumbai (best guess)` + advisory with `best-guess`
- [x] Unknown input never raises, never substitutes silently (disclosure fields always set)
- [x] Empty key → live `open-meteo` source; `SECRET_PROBE_42` in neither JSON nor logs
- [x] COVERAGE.md exists with INTEGRATE + OPT-OUT sections, every OPT-OUT row with a reason
- [x] Full suite + coverage report green (evidence above)
- [ ] Commits exist — **FAILED (environment)**, documented above; no code impact
