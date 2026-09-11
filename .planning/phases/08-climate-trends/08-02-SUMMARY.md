---
phase: 08-climate-trends
plan: 02
subsystem: climate-trends
tags: [open-meteo-archive, trend-cache, fallback-disclosure, climate-strip, coverage-matrix, pytest, tsc, next-build]

# Dependency graph
requires:
  - phase: 08-climate-trends plan 01
    provides: get_climate_trends tracer plus archive fetch/mapping plus fixture plus mocked-LLM number-match
  - phase: 02-imd-live-data
    provides: cache/fallback/disclosure discipline plus MockTransport seam
  - phase: 03-forecast-alerts
    provides: tuple-key namespacing plus forecast cache precedent
provides:
  - Trend cache on tuple key (climate, lookup_key) with 600s TTL plus stale-serve plus empty-cache fallback
  - ClimateStrip landing component plus page assembly after AlertsShowcase
  - Phase 2 and Phase 3 COVERAGE INTEGRATE rows for the daily-archive trend capability
affects: [08-climate-trends seal-time gate, demo-readiness, MoES climate-information gap]

# Actuals — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 5100
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 0682a22849aa1b58f2bab7dc201922c7285178d6

# Tech tracking
tech-stack:
  added: []
  patterns: [tuple-key-cache-namespacing, stale-serve-plus-fallback-parity, showcase-pattern-strip]

key-files:
  created: [frontend/components/climate-strip.tsx]
  modified: [tools/weather.py, tests/test_climate_trends.py, frontend/app/page.tsx, .planning/phases/02-imd-live-data/COVERAGE.md, .planning/phases/03-forecast-alerts/COVERAGE.md]

key-decisions:
  - "Trend cache key is the tuple (climate, lookup_key) so it can never collide with current plain-string or forecast tuple keys"
  - "Empty-cache trend fallback carries both note and advisory with the literal fallback sentence plus window_days 30 and mock non-IMD source"
  - "ClimateStrip reuses alerts-showcase wrapper/kicker/section-title/glass-card tokens exactly, no new colors or gradients, per D-05"
  - "Coverage files record the archive capability as INTEGRATE with reason citing archive-api.open-meteo.com past_days 30 and daily max/min/precip"

patterns-established:
  - "Trend outage parity: stale-serve stamped plus-stale-fallback with advisory fallback note, else mock-shaped 30-day fallback; neither branch pins the cache"
  - "Strip assembly: ClimateStrip immediately after AlertsShowcase and before HowItWorks with all other sections unmoved"

requirements-completed: [CLIM-02, CLIM-03]

# Coverage metadata — drives deterministic UAT routing in verify-work.
coverage:
  - id: D1
    description: "Repeated trend queries hit a 10-minute cache; archive outages degrade exactly like the current path with stamped mock plus disclosed fallback note"
    requirement: "CLIM-02"
    verification:
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_cache_hit_single_transport_hit"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_ttl_expiry_forces_refetch"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_stale_serve_on_outage"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_empty_cache_fallback_disclosure"
        status: pass
    human_judgment: false
  - id: D2
    description: "Trend replies always disclose the 30-day window plus non-IMD sourcing, including cached, stale, and fallback cases"
    requirement: "CLIM-02"
    verification:
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_stale_serve_on_outage"
        status: pass
      - kind: unit
        ref: "tests/test_climate_trends.py#test_trend_empty_cache_fallback_disclosure"
        status: pass
    human_judgment: false
  - id: D3
    description: "Landing page shows a compact climate strip with real copy and zero lorem reusing the alerts-showcase pattern, all gates green"
    requirement: "CLIM-03"
    verification:
      - kind: unit
        ref: "npx tsc --noEmit in frontend (exit 0)"
        status: pass
      - kind: e2e
        ref: "temp-dir npm run build: Compiled successfully, 5/5 static pages, / 10.8 kB, /chat 7.71 kB"
        status: pass
      - kind: unit
        ref: "node --test frontend/lib/__tests__/chat-contract.test.mjs (21/21 pass)"
        status: pass
    human_judgment: false

# Metrics
duration: 20min
completed: 2026-09-11
status: complete
---

# Phase 8 Plan 02: Trend Hardening Plus Climate Strip Summary

**Hardened 30-day trends with 10-minute tuple-key cache plus stamped disclosed fallback parity, and a showcase-pattern climate strip on landing (rain 157.2 mm, mean 27.02 C) with coverage INTEGRATE and every gate green**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-11T20:25:00Z
- **Completed:** 2026-09-11T20:42:44Z
- **Tasks:** 3
- **Files modified:** 6 (1 created, 5 edited)

## Accomplishments

- Trend cache plus fallback hardening in `tools/weather.py`: tuple key `(climate, lookup_key)` with 600s TTL, `_decorate_hit` on hit, `_decorate_stale` plus-stale-fallback on outage with cache, mock-shaped 30-day fallback with literal note on empty cache; neither error branch pins the cache
- Four new MockTransport-only tests proving single-transport-hit caching, TTL-expiry refetch, stale-serve stamping with advisory note, and empty-cache disclosure (window_days 30, mock plus non-IMD, rain 0.0, empty dates); full suite 90 passed, 1 skipped
- `ClimateStrip` landing component mirroring `alerts-showcase` wrapper/kicker/section-title/glass-card with real copy (rain sum, mean/min/max, wettest 2026-08-23/driest 2026-08-13, non-IMD footnote) and zero lorem/gradient; assembled in `page.tsx` after `AlertsShowcase` before `HowItWorks`
- Phase 2 and Phase 3 `COVERAGE.md` rows flipped to INTEGRATE with reason citing `get_climate_trends` via `archive-api.open-meteo.com` past_days 30 and daily max/min/precip behind the `imd_client` seam, MockTransport plus fixtures only in CI, disclosed non-IMD
- Full ordered battery green: pytest, tsc, temp-dir production build, slop grep, contract test 21/21, coverage grep

## Task Commits

Each task was committed atomically:

1. **Task 1: Trend cache plus fallback and disclosure hardening** - `6a3e9fe` (feat)
2. **Task 2: Climate strip component plus landing assembly** - `284ed5b` (feat)
3. **Task 3: Coverage integration plus full gate battery** - `660f0f5` (docs)

## Files Created/Modified

- `tools/weather.py` - Tuple-key trend cache, stale-serve, empty-cache fallback with advisory parity; fresh-only store
- `tests/test_climate_trends.py` - Four hardening tests (hit, expiry, stale, fallback disclosure) plus counting-transport helper
- `frontend/components/climate-strip.tsx` - New ClimateStrip strip in the showcase pattern with real copy and non-IMD footnote
- `frontend/app/page.tsx` - Import plus render ClimateStrip after AlertsShowcase before HowItWorks
- `.planning/phases/02-imd-live-data/COVERAGE.md` - Archive trend capability INTEGRATE row with get_climate_trends plus host
- `.planning/phases/03-forecast-alerts/COVERAGE.md` - Same INTEGRATE row for the forecast-phase matrix

## Decisions Made

- Tuple key `(climate, lookup_key)` chosen to namespace trend entries away from current plain-string keys and forecast `("forecast", ...)` keys per T-08-05; verified by asserting both key shapes in the hit test.
- Empty-cache fallback carries both `note` and `advisory` with the identical literal fallback sentence so stale and fallback states disclose alike per T-08-06; `deviation_note` keeps the richer "Trend data unavailable; showing fallback values." wording which contains the plan's "Trend data unavailable" prefix.
- Strip badges reuse existing palette tokens only (teal-700, amber-600, slate-500 families already present in teaser/moes/showcase) with no gradient utilities and no new fonts or colors per anti-slop bans and T-08-07; no IMD-issued wording anywhere in the strip.
- Coverage rows cite the exact archive host, past_days 30, and daily field list so the seal-time gate sees the decision without re-deriving it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added advisory to the empty-cache trend fallback**
- **Found during:** Task 1 (trend hardening)
- **Issue:** Plan action requires the fallback advisory to prefix the literal `_FALLBACK_NOTE` sentence and threat T-08-06 requires advisory to always surface the note, but the Plan 01 `_fallback_trend_payload` carried only `note` with no `advisory` key; stale payloads via `_decorate_stale` do carry `advisory`, so fallback would disclose unlike stale.
- **Fix:** Added an `advisory` key mirroring the `note` text (literal fallback sentence plus archive location plus non-IMD) in `_fallback_trend_payload`; updated docstring to record the never-store-as-fresh invariant.
- **Files modified:** tools/weather.py
- **Verification:** `test_trend_empty_cache_fallback_disclosure` asserts the literal note in both `note` and `advisory`; pytest 90 passed
- **Committed in:** 6a3e9fe (Task 1 commit)

**2. [Rule 3 - Blocking] Resolved plan file-path mismatches for coverage and tests**
- **Found during:** Tasks 1 and 3 (read_first)
- **Issue:** Plan frontmatter `files_modified` lists `.planning/phases/02-imd-live-data/02-COVERAGE.md` and `.planning/phases/03-forecast-alerts/03-COVERAGE.md` plus omits `tests/test_climate_trends.py`, but the repo carries `COVERAGE.md` (no 02-/03- prefix) and the Task 1 action mandates extending `tests/test_climate_trends.py`. Strictly touching only `files_modified` would miss both required edits.
- **Fix:** Edited the actual `COVERAGE.md` files (the clearly intended targets) and extended `tests/test_climate_trends.py` per the task action; left the non-existent 02-/03- paths untouched.
- **Files modified:** .planning/phases/02-imd-live-data/COVERAGE.md, .planning/phases/03-forecast-alerts/COVERAGE.md, tests/test_climate_trends.py
- **Verification:** Coverage grep finds `get_climate_trends` plus `archive-api.open-meteo.com` in both files; pytest green
- **Committed in:** 6a3e9fe (tests), 660f0f5 (coverage)

---

**Total deviations:** 2 auto-fixed (1 missing-critical, 1 blocking)
**Impact on plan:** Both required to meet the plan's own acceptance criteria and threat mitigations. No scope creep; current/forecast/agent behavior untouched.

## Issues Encountered

- Windows read-only flags on `tools/weather.py`, `tests/test_climate_trends.py`, `frontend/app/page.tsx`, and both `COVERAGE.md` files: cleared first via `attrib -R <file>` (one file per call) before editing, per plan and environment notes.
- Git tracks only a sparse subset (8 files before this plan); `frontend/app/page.tsx`, `frontend/components/climate-strip.tsx`, and both `COVERAGE.md` files were previously untracked, so their Task 2/3 commits record full-file adds rather than diffs. No work blocked; noted for the verifier.
- No `gsd_run` state calls per the execution brief (explicit "No gsd_run state calls"); STATE/ROADMAP advancement left to the orchestrator.
- `.pytest_cache` permission warnings on every pytest run (cache write denied); harmless, tests pass.
- H:/ denies deletion so the production build ran in `C:/Users/USER/AppData/Local/Temp/weathergpt-build-0802/frontend` via robocopy (source minus node_modules/.next plus node_modules copy); in-place build never attempted.

## User Setup Required

None - no external service configuration required. No live network in tests (MockTransport plus fixtures only); no new npm or pip packages installed per T-08-SC.

## Threat Flags

None beyond the plan's `<threat_model>`: no new network endpoints (archive host is the plan-sanctioned provider), no auth paths, no schema changes at trust boundaries. Mitigations T-08-05 (tuple key, lock-guarded access, never stores error payloads), T-08-06 (stale plus-stale-fallback with age plus literal note in advisory; empty-cache mock plus non-IMD with literal note in note plus advisory), T-08-07 (strip footnote discloses non-IMD model aggregates, no IMD-issued wording, zero-lorem grep gate), and T-08-SC (no installs; build plus tsc on vendored toolchain) are all implemented.

## Gate Evidence

- `python -m pytest tests/ -q`: 90 passed, 1 skipped (pre-existing live-OpenRouter skip), 1 harmless pytest-cache warning
- `npx tsc --noEmit` in frontend: exit 0 (also TSC-OK after strip edit)
- Temp-dir production build in `C:/Users/USER/AppData/Local/Temp/weathergpt-build-0802/frontend`: `npm run build` exit 0, `Compiled successfully`, `Generating static pages (5/5)`, `/` 10.8 kB / 115 kB first load, `/chat` 7.71 kB / 112 kB, zero type errors
- Slop scan over `frontend/components/climate-strip.tsx` and `frontend/app/page.tsx`: `lorem` zero matches, gradient clichés (`from-purple|to-blue|via-purple|bg-gradient|purple.*blue`) zero matches
- `node --test frontend/lib/__tests__/chat-contract.test.mjs`: 21/21 pass (4 suites)
- Coverage grep: both `COVERAGE.md` files contain `get_climate_trends` plus `archive-api.open-meteo.com` (one INTEGRATE row each)

## Next Phase Readiness

- Demo-grade trends ready: cached, stale, and fallback states all disclose 30-day window plus non-IMD sourcing; landing shows the climate strip in the showcase pattern.
- No blockers. Current, forecast, and agent-orchestration behavior otherwise untouched (full-suite no-regression evidence above).
- Seal-time gate can read the archive INTEGRATE decision from both coverage matrices.

## Self-Check: PASSED

- FOUND: tools/weather.py, tests/test_climate_trends.py, frontend/components/climate-strip.tsx, frontend/app/page.tsx, .planning/phases/02-imd-live-data/COVERAGE.md, .planning/phases/03-forecast-alerts/COVERAGE.md, .planning/phases/08-climate-trends/08-02-SUMMARY.md
- Commits verified in `git log`: 6a3e9fe, 284ed5b, 660f0f5
- Pinned aggregates re-verified: rain_sum 157.2, temp_mean 27.02, wettest 2026-08-23, driest 2026-08-13, window 30 days
- Measured commits from ledger: `git rev-list --count 0682a22..HEAD` = 3

---
*Phase: 08-climate-trends*
*Completed: 2026-09-11*
