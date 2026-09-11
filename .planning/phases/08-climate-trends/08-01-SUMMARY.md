---
phase: 08-climate-trends
plan: 01
subsystem: climate-trends
tags: [open-meteo-archive, langchain-tool, agent-grounding, pytest, mock-transport]

# Dependency graph
requires:
  - phase: 02-imd-live-data
    provides: fetch/mapping/cache/fallback patterns plus MockTransport fixture seam
  - phase: 03-forecast-alerts
    provides: forecast daily-aggregate mapping precedent plus _TOOLS wiring pattern
provides:
  - Archive fetch (fetch_archive_open_meteo) plus aggregate mapping (map_archive_to_payload) in tools/imd_client.py
  - get_climate_trends tool in tools/weather.py with fresh stamps plus stamped mock fallback
  - Agent registration plus single trend prompt rule (rule 11) in services/agent.py
  - Pune 30-day archive fixture plus mocked-LLM number-match tests in tests/test_climate_trends.py
affects: [08-climate-trends plan 02 (cache/fallback/disclosure hardening, climate strip, page assembly)]

# Actuals — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 12000
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns: [archive-daily-aggregate-mapping, tool-JSON-number-match-test, best-guess-disclosure-reuse]

key-files:
  created: [tests/fixtures/open_meteo_archive_pune.json, tests/test_climate_trends.py]
  modified: [tools/imd_client.py, tools/weather.py, services/agent.py, tests/test_agent_agri.py, tests/test_forecast_alerts.py]

key-decisions:
  - "window_days reports days actually aggregated (30 on the full happy path)"
  - "Trend tool returns fresh-only in the tracer; cache hardening deferred to Plan 02"
  - "Stale 2-tool _TOOLS assertions updated to the intended 3-tool registry"

patterns-established:
  - "Archive mapping: defensive .get parsing with safe defaults, short arrays map available days, wholly missing daily raises sanitized RuntimeError"
  - "Trend fallback: stamped mock-climate-fallback with stale True, mirroring the current-tool outage contract"

requirements-completed: [CLIM-01, CLIM-02]

# Coverage metadata — drives deterministic UAT routing in verify-work.
coverage:
  - id: D1
    description: "Pune 30-day trend flows fixture through archive fetch and mapping to get_climate_trends JSON with exact aggregates and non-IMD source"
    requirement: "CLIM-01"
    verification:
      - kind: unit
        ref: "tests/test_climate_trends.py#test_mapping_aggregates_match_fixture"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_tool_json_contract"
        status: pass
    human_judgment: false
  - id: D2
    description: "Agent exposes get_climate_trends with one new prompt rule; current/forecast behavior untouched"
    requirement: "CLIM-02"
    verification:
      - kind: unit
        ref: "tests/test_climate_trends.py#test_tool_fresh_stamps"
        status: pass
    human_judgment: false
  - id: D3
    description: "Mocked-LLM trend reply quotes exact fixture numbers with 30-day plus non-IMD disclosure; outage yields stamped mock fallback"
    requirement: "CLIM-02"
    verification:
      - kind: integration
        ref: "tests/test_climate_trends.py#test_mocked_llm_reply_quotes_exact_numbers"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_archive_outage_yields_stamped_fallback"
        status: pass
    human_judgment: false

# Metrics
duration: 25min
completed: 2026-09-11
status: complete
---

# Phase 8 Plan 01: Pune 30-Day Archive Trend Tracer Summary

**End-to-end 30-day Pune climate trend behind the IMD-shaped seam: archive fetch plus rain/temp aggregates plus get_climate_trends tool plus one agent rule, proven by a mocked-LLM number-match test (rain 157.2 mm, mean 27.02 C, wettest 2026-08-23)**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-11T12:00:00Z
- **Completed:** 2026-09-11T12:25:00Z
- **Tasks:** 3
- **Files modified:** 7 (3 created, 4 edited)

## Accomplishments

- Archive fetch (`fetch_archive_open_meteo`, past_days 30, daily max/min/precip) plus aggregate mapping (`map_archive_to_payload`: rain sum, temp mean/min/max, wettest/driest days, deviation note, window dates, non-IMD source) in `tools/imd_client.py`
- `get_climate_trends` langchain tool in `tools/weather.py` reusing CITY_COORDS, 120-char cap, latlon parse, and Mumbai best-guess disclosure; fresh stamps on success, stamped mock fallback on outage
- Agent registration plus exactly one new prompt rule (rule 11) in `services/agent.py`; existing rules, tools order, `_derive_alert_level`, and retry logic untouched
- Hand-authored 30-day Pune fixture plus 5-test suite incl. mocked-LLM test proving the reply embeds exact tool numbers with 30-day plus non-IMD disclosure; full suite green (86 passed, 1 pre-existing live-test skip)

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end 30-day trend for Pune** - `2f502c3` (feat)
2. **Task 2: Agent registration plus one trend prompt rule** - `40a0cb3` (feat)
3. **Task 3: Mocked-LLM number-match test** - `fe8c34e` (test)

## Files Created/Modified

- `tools/imd_client.py` - Archive endpoint constants, `fetch_archive_open_meteo`, `map_archive_to_payload`
- `tools/weather.py` - `get_climate_trends` tool plus `_fallback_trend_payload` plus `_apply_trend_guess_note`
- `services/agent.py` - `get_climate_trends` import, `_TOOLS` entry, SYSTEM_PROMPT rule 11
- `tests/fixtures/open_meteo_archive_pune.json` - Hand-authored 30-day daily arrays for Pune (18.5204, 73.8567), 2026-08-12 to 2026-09-10
- `tests/test_climate_trends.py` - Mapping, tool contract, fresh-stamp, mocked-LLM number-match, and outage tests
- `tests/test_agent_agri.py` - `_TOOLS` length assertion updated 2 to 3 (deviation, see below)
- `tests/test_forecast_alerts.py` - Tool registry assertion updated to the 3-tool set (deviation, see below)

## Decisions Made

- `window_days` reports the days actually aggregated (30 on the full happy path) rather than a hardcoded 30, so short-array degradation stays truthful while the fixture path carries exactly 30.
- Trend tool returns fresh-only in this tracer (no cache read/write); cache/fallback/disclosure hardening is explicitly Plan 02 scope per the plan.
- Stale 2-tool `_TOOLS` assertions updated to the intended 3-tool registry (deviation Rule 1, below); no production behavior beyond the planned registration.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated two stale tests pinning the pre-trend 2-tool registry**
- **Found during:** Task 3 (full-suite verification)
- **Issue:** `tests/test_agent_agri.py::test_system_prompt_agri_rules_reference_tools_and_curated_base` asserted `len(_TOOLS) == 2` and `tests/test_forecast_alerts.py::test_agent_tools_registered` asserted the exact 2-tool name set. Both failed after the plan-mandated Task 2 registration of `get_climate_trends` in `_TOOLS` (2 failed, 84 passed).
- **Fix:** Minimal assertion updates only: length 2 to 3 (with a Phase 8 comment) and the name set extended with `get_climate_trends`. No production code touched; the pinned single literal mention of `get_weather_forecast` still holds.
- **Files modified:** tests/test_agent_agri.py, tests/test_forecast_alerts.py
- **Verification:** `python -m pytest tests/ -q` green: 86 passed, 1 skipped (pre-existing live-OpenRouter skip)
- **Committed in:** fe8c34e (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug/stale-test)
**Impact on plan:** Required to reconcile pre-existing assertions with the plan's own mandated end state. No scope creep; current/forecast byte-behavior unchanged.

## Issues Encountered

- Windows read-only flags on `tools/imd_client.py`, `tools/weather.py`, `services/agent.py`, and the two edited test files: cleared first via `attrib -R <file>` (single file per call) before editing, per plan acceptance criteria.
- Stale git locks (`.git/index.lock`, `.git/config.lock`) plus missing repo author identity blocked the first commit attempts: cleared the stale locks (no git process running), set a repo-local `user.name`/`user.email` (no global config touched), and all three task commits landed. Best-effort git per execution brief; no work was blocked.
- `.pytest_cache` permission warnings appear on every pytest run (cache write denied); harmless, tests themselves pass.

## User Setup Required

None - no external service configuration required. No live network in tests (MockTransport plus recorded fixture); no new packages installed.

## Threat Flags

None beyond the plan's `<threat_model>`: no new network endpoints (archive host is the plan-sanctioned provider), no auth paths, no schema changes at trust boundaries. Mitigations T-08-01 (defensive parsing, short-array tolerance, `_as_float` NaN/inf guard), T-08-02 (log-full/send-safe fetch errors), T-08-03 (non-IMD marker end-to-end in `ARCHIVE_SOURCE` plus rule 11 plus reply text), and T-08-04 (argmax/argmin-derived dates pinned by the number-match test) are all implemented; T-08-SC holds (no installs).

## Next Phase Readiness

- Tracer complete: fixture to tool JSON to mocked-LLM reply proven with exact numbers; Plan 02 can harden cache/fallback/disclosure and build the climate strip on this seam.
- No blockers. Current/forecast/agent behavior otherwise untouched (full-suite no-regression evidence above).

## Self-Check: PASSED

- FOUND: tools/imd_client.py, tools/weather.py, services/agent.py, tests/fixtures/open_meteo_archive_pune.json, tests/test_climate_trends.py
- Commits verified in `git log`: 2f502c3, 40a0cb3, fe8c34e
- Pinned aggregates re-verified from the fixture: rain_sum 157.2, temp_mean 27.02, temp_min 23.0, temp_max 32.0, wettest 2026-08-23, driest 2026-08-13

---
*Phase: 08-climate-trends*
*Completed: 2026-09-11*
