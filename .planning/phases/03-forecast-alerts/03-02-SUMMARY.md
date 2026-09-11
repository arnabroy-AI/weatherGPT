# Phase 03 Plan 02: Per-Day Advisories + Rollup + Minimal Agent Wiring Summary

**Status:** complete — all 2 tasks done, `tests/test_forecast_alerts.py` 11/11 green, combined forecast files 19/19 green, full suite 55 passed + 1 skipped (pre-existing skip), zero regressions.

## What was built

Per-day Orange/Red safety advisories plus one trip-level rollup line in the forecast payload (D-05), reusing the vetted `_build_advisory` texts with no forked severity wording, and the minimal agent wiring (D-08): tool registration plus exactly one prompt rule. No orchestration, no `weather.py` changes, no `_build_advisory` body changes.

- `tools/imd_client.py` — extended `map_forecast_to_payload` (Plan 01 body otherwise untouched): each day entry gains an `advisory` string built by calling the existing `_build_advisory` with the day `alert_level`, day `condition`, and a `"<location> on <date>"` label (falls back to bare location when the date is empty; the 80-char caps inside `_build_advisory` still apply). Added top-level `rollup_advisory`: calm forecasts state `No severe weather expected in <location> from <first> to <last> (non-IMD model data)`; severe forecasts state `<worst> conditions worst on <weekday> (<date>) near <location> (non-IMD model estimate). Orange/Red on <dates>; reconsider outdoor plans on those days.` `alert_line` construction is byte-identical to Plan 01 (D-04).
- `services/agent.py` — `from tools.weather import get_current_weather, get_weather_forecast`; `_TOOLS = [get_current_weather, get_weather_forecast]`; exactly one new SYSTEM_PROMPT rule (rule 7): multi-day/weekend/trip forecast questions call `get_weather_forecast` with the best location and requested day count. No other agent changes.
- `tests/test_forecast_alerts.py` — 11 tests, no live network (fixture dicts fed directly to the mapper): Orange advisory text, Red advisory text, Green calm wording, severe rollup (worst level + weekday + severe dates + trip guidance), calm rollup (no-severe + location + span), `alert_line` format regression, `_TOOLS` membership (exactly both tools), single prompt rule, Orange/Red `_derive_alert_level` parse proofs, and a mapper-line round-trip parse (actual `alert_line` → worst level) plus JSON-serializability.

## Verification evidence

- `python -m pytest tests/test_forecast_alerts.py -q` → **11 passed** (3.36s)
- `python -m pytest tests/test_forecast_alerts.py tests/test_forecast.py -q` → **19 passed** (11 new + 8 Plan 01 tracer, zero regressions)
- `python -m pytest tests/ -q` → **55 passed, 1 skipped** (8.16s; skip is pre-existing). Note: 6 of the 55 come from `tests/test_forecast_cache.py`, the concurrently-running Plan 03's file present on disk — all green, no conflicts; my plan contributes 11.
- Spot-checks: fixture Orange day advisory contains "Avoid unnecessary travel"; Red-mutated day contains "Avoid travel and stay indoors"; severe rollup e.g. `Orange conditions worst on Mon (2026-09-15) near Mumbai (non-IMD model estimate). Orange/Red on 2026-09-15; reconsider outdoor plans on those days.`; calm rollup e.g. `No severe weather expected in Mumbai from 2026-09-12 to 2026-09-16 (non-IMD model data).`

## Deviations from plan

None — plan executed exactly as written. Per-day advisories reuse `_build_advisory` with zero body changes; `alert_line` untouched; agent change is import + list entry + one prompt line; `tools/weather.py` not modified (per-day advisories flow to the tool automatically since it copies `mapped["days"]`; top-level `rollup_advisory` lives on the mapper payload per the artifact spec).

## Git commits (BEST-EFFORT — blocked, noted per instructions)

No commit was possible: the repo has no commits yet and `git status` shows the entire tree untracked (no HEAD to commit onto; same pre-existing condition as 03-01). Per environment notes I did not block on this. Files changed (uncommitted, verified present on disk): `tools/imd_client.py` (edited), `services/agent.py` (edited), `tests/test_forecast_alerts.py` (new).

## Known stubs / threat flags

None. No `TODO`/`placeholder`/empty-value stubs introduced; no new network endpoints, auth paths, or dependencies (per T-03-SC, no installs). STRIDE mitigations hold: T-03-04 (advisories reuse vetted wording, 80-char caps preserved, never IMD-issued — both per-day and rollup carry the non-IMD qualifier), T-03-05 (registration only, location handling untouched with the existing 120-char cap in `weather.py`).

## DoD mapping

- Orange/Red days each carry 1–2 line safety advisories + one overall rollup line: ✅ (mapper `advisory` per day + `rollup_advisory`, 5 advisory/rollup tests)
- Agent lists the forecast tool with one prompt rule: ✅ (`_TOOLS` equality + single-mention prompt tests)
- Worst-day Alert line parses through the unchanged Phase 1 regex: ✅ (Orange + Red + live-mapper round-trip parse, `_derive_alert_level` untouched)

## Self-Check: PASSED

- `tools/imd_client.py` per-day `advisory` + `rollup_advisory` present; `_build_advisory` body untouched; `alert_line` construction unchanged.
- `services/agent.py` import + `_TOOLS` + single prompt rule present; `SYSTEM_PROMPT.count("get_weather_forecast") == 1` (file-wide count is 3: import, list, prompt — as specified).
- `tests/test_forecast_alerts.py` present with 11 green tests; full suite 55 passed + 1 pre-existing skip.
- No commits to verify (commit blocked — documented above, not a code gap).
