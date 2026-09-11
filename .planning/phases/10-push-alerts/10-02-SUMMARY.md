---
phase: 10-push-alerts
plan: 02
subsystem: push-notifications
tags: [watcher, dedup, fcm-routes, sentinel, coverage-matrix]

# Dependency graph
requires:
  - phase: 10-push-alerts
    provides: [FCM v1 dispatch slice with bearer seam, MockTransport test philosophy, sentinel-test pattern]
  - phase: 02-imd-live-data
    provides: [derive_alert_level sole threshold authority, cached get_current_weather seam, CITY_COORDS 18-city map]
provides:
  - Hourly 18-city watcher with 6h dedup and upgrade re-fire
  - Alert routes (subscribe/send/check/status) with throttle plus sanitize plus 422/502 mapping
  - FCM secret-safety sentinel suite plus validate_only live opt-in plus coverage matrix
affects: [ship-gate FCM matrix, v2 persistent registry]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 16812
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns: [cached-seam evaluate with no second heuristic, monotonic dedup with upgrade bypass, cron-callable check route, suffix-only token echo]

key-files:
  created: [backend/services/alert_watcher.py, backend/schemas/alerts.py, backend/tests/test_alert_watcher.py, backend/tests/test_fcm_secrets.py, backend/tests/test_live_fcm.py, .planning/phases/10-push-alerts/10-COVERAGE.md]
  modified: [backend/api/routes.py, backend/.env.example]

key-decisions:
  - "Watcher trigger is callable run_watch_cycle plus POST /api/alerts/check as the hourly cron target — no in-process scheduler, stdlib-only posture kept"
  - "Registry is lock-guarded in-memory set plus dict (D-02, no DB in v1); status/subscribe echo at most token last-6 plus counts"
  - "should_dispatch records on True so the dedup sequence is observable; run_watch_cycle rolls back the record when the send fails so a failed send never suppresses the next cycle"

patterns-established:
  - "Dedup: per location-plus-level timestamp plus per-location last-level record on monotonic time; 21600 s cooldown on repeats, strict-severity upgrade bypass"
  - "Fan-out: default send posts the topic then best-effort direct sends to subscribed tokens; per-token failure logged and continued"
  - "Send route enforces Orange-Red-only before loading the service account, so Green/Yellow never touch disk or network"

requirements-completed: [NOTF-01, NOTF-02]

# Coverage metadata (#1602)
coverage:
  - id: E1
    description: "Watcher evaluates all 18 cities through the cached seam; Orange surfaces with one upstream hit across two calls"
    requirement: "NOTF-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_alert_watcher.py#test_evaluate_city_orange_via_cached_seam_single_hit"
        status: pass
    human_judgment: false
  - id: E2
    description: "6h dedup matrix: first Orange fires, repeat suppressed, Orange-to-Red upgrade re-fires, Green/Yellow never fire, Red-to-Orange downgrade suppressed"
    requirement: "NOTF-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_alert_watcher.py#test_dedup_matrix_upgrade_refires_immediately"
        status: pass
    human_judgment: false
  - id: E3
    description: "Subscribe/send/check/status routes enforce throttle plus sanitize plus 422/502 mapping with key-free bodies"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_alert_watcher.py#test_route_send_orange_token_200"
        status: pass
    human_judgment: false
  - id: E4
    description: "Three-sentinel FCM suite clean on errors, bodies, and logs across direct send plus send/check/status routes"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_fcm_secrets.py#test_check_route_outage_leaks_no_keys"
        status: pass
    human_judgment: false

# Metrics
duration: 35min
completed: 2026-09-12
status: complete
---

# Phase 10 Plan 02: Watcher plus Registry plus Alert Routes Summary

**In-memory registry with subscribe endpoints, hourly 18-city watcher with 6h dedup and instant upgrade re-fire, four throttle-guarded routes, sentinel suite, validate_only live opt-in, and decided coverage matrix**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-12T01:00:00+05:30
- **Completed:** 2026-09-12T01:35:00+05:30
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- `backend/services/alert_watcher.py` — `WATCH_CITIES` (18, derived from `CITY_COORDS`), `DISPATCH_LEVELS` (Orange/Red), `COOLDOWN_S` (21600); lock-guarded registry (`subscribe`/`unsubscribe`/`registry_counts`); `evaluate_city` via the cached `get_current_weather` seam (no second heuristic); monotonic `should_dispatch` with upgrade bypass; `run_watch_cycle(send_fn, now)` returning `{checked, dispatched, skipped}` and never raising on a single-city failure; `reset_for_tests`
- `backend/schemas/alerts.py` — `SubscribeRequest` (token 2048, topics 32), `SendRequest` (one-of token/topic, title 200, body 1000, location 120), `CheckResponse`, `StatusResponse`
- `backend/api/routes.py` — `POST /api/alerts/subscribe` (suffix-only echo), `POST /api/alerts/send` (exactly-one-target, Orange-Red-only 422, missing-file 502 naming the file, message-name 200), `POST /api/alerts/check` (hourly cron target, `checked: 18`), `GET /api/alerts/status` (18 cities, 6h, counts, `fcm_configured`, zero token bytes) — all behind `check_rate_limit` plus `sanitize_detail` plus 422/502/500 mapping
- `backend/.env.example` — `FCM_SERVICE_ACCOUNT_FILE=fcm-service-account.json` with missing-file-disables-cleanly plus gitignored comment
- `backend/tests/test_alert_watcher.py` — 23 tests: constants pin, sole-authority proof, registry, full dedup matrix, cached-seam single-hit Orange, failure-None, cycle dispatch/dedup/Green/failure-isolation, 8 route tests
- `backend/tests/test_fcm_secrets.py` — 4 tests: three sentinels (private key, access token, device token) clean across direct-500, send-route 502, Orange-check-against-500 plus status, plus `sanitize_detail` carryover unit check
- `backend/tests/test_live_fcm.py` — skipped by default, `RUN_LIVE_FCM=1` opt-in sending one benign Orange topic payload with `validate_only: true` (nothing delivers)
- `.planning/phases/10-push-alerts/10-COVERAGE.md` — 3 INTEGRATE rows (token send NOTF-01, topic send NOTF-01, threshold evaluation NOTF-02) plus exactly the SMS/WhatsApp OPT-OUT row plus notes (6h/upgrade, google-auth opt-in with zero new deps, validate_only posture, key-never-logged)
- Gates: `pytest tests/test_alert_watcher.py -q` → 23 passed; `-k route` → 8 passed; `pytest tests/test_fcm_secrets.py -q` → 4 passed; full `pytest tests/ -q` → 151 passed, 3 skipped (2 pre-existing live + 1 live-FCM)
- Scope proof: `backend/requirements.txt` SHA256 unchanged (`00E5DF9B…C72925`) — zero new runtime deps (T-10-SC)

## Task Commits

Each task was committed atomically:

1. **Task 1: Watcher: registry plus cached-seam evaluate plus 6h dedup** - `fe9d094` (feat) + `b6a0cf9` (fix: threshold-authority wording kept literal-free)
2. **Task 2: Routes: subscribe plus send plus check plus status with throttle and sanitize** - `edab2b4` (feat)
3. **Task 3: Seal: watcher tests plus sentinel suite plus coverage matrix plus live opt-in** - `829f816` (test)

## Files Created/Modified

- `backend/services/alert_watcher.py` - registry plus evaluate plus monotonic dedup plus 18-city cycle (created)
- `backend/schemas/alerts.py` - alert request/response shapes with length caps (created)
- `backend/api/routes.py` - four alert endpoints reusing throttle/sanitize/error mapping (modified)
- `backend/.env.example` - FCM service-account file doc line (modified)
- `backend/tests/test_alert_watcher.py` - dedup matrix plus cached-seam plus route battery (created)
- `backend/tests/test_fcm_secrets.py` - three-sentinel errors/bodies/logs suite (created)
- `backend/tests/test_live_fcm.py` - validate_only opt-in live test, skipped by default (created)
- `.planning/phases/10-push-alerts/10-COVERAGE.md` - FCM coverage matrix with SMS/WhatsApp OPT-OUT (created)

## Decisions Made

- Watcher trigger is callable `run_watch_cycle` plus `POST /api/alerts/check` as the documented hourly cron target — no in-process scheduler, stdlib-only posture kept (planner's recorded discretion)
- `should_dispatch` records on True (observable dedup sequence); `run_watch_cycle` snapshots and rolls back that record when the fan-out send fails, so a failed send retries next cycle instead of suppressing for 6h
- Send route validates Orange-Red-only and exactly-one-target before loading the service account, so misuse fails fast with 422 without touching disk or network
- Coverage matrix carries exactly one OPT-OUT row (SMS/WhatsApp, no-credentials-plus-DLT reason) per plan; no other capability is opted out

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pydantic StructuredTool has no patchable `invoke` field**
- **Found during:** Task 3, `test_evaluate_city_failure_returns_none`
- **Issue:** `monkeypatch.setattr(get_current_weather, "invoke", ...)` raised `ValueError: StructuredTool object has no field invoke`
- **Fix:** Replaced the module attribute with a stub seam object (`_BoomSeam` with a raising `invoke`) instead of patching the tool's field
- **Files modified:** `backend/tests/test_alert_watcher.py`
- **Commit:** `829f816`

**2. [Rule 1 - Bug] Sole-authority substring test tripped on the watcher's own docstring**
- **Found during:** Task 3, `test_no_second_heuristic_in_watcher`
- **Issue:** The watcher docstring/comment named the threshold function for documentation, so a naive `in source` assertion failed on prose rather than on a call
- **Fix:** Reworded the watcher prose to reference the authority without the literal, and hardened the test to assert no import/call/redefinition (`from tools.imd_client import`, `imd_client.derive`, `def derive_alert_level`, `derive_alert_level(`)
- **Files modified:** `backend/services/alert_watcher.py`, `backend/tests/test_alert_watcher.py`
- **Commit:** `b6a0cf9` (watcher), `829f816` (test)

Otherwise none — plan executed as written. No architectural changes, no new dependencies, no auth gates.

## Issues Encountered

- None blocking. Pre-existing repo modifications outside this plan's scope (`.gitignore`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, assorted untracked planning/frontend files) were left untouched and uncommitted.

## User Setup Required

None - no external service configuration required. Live FCM validation remains a documented opt-in (`RUN_LIVE_FCM=1` + valid `FCM_SERVICE_ACCOUNT_FILE` + `pip install google-auth`); all CI tests are mocked. Hourly operation is `POST /api/alerts/check` on a cron (documented in the watcher module).

## Next Phase Readiness

- NOTF-01 plus NOTF-02 are complete per D-01/D-02/D-03: 18-city Orange/Red watcher, 6h dedup with upgrade re-fire, registry plus four operable endpoints, sentinel-clean secrets, decided coverage matrix, green full suite
- Watch items: registry is in-memory (persistent DB deferred to v2 per CONTEXT); SMS/WhatsApp stays OPT-OUT (needs keys + DLT); frontend subscribe UI out of scope (endpoints only)
- Real `backend/fcm-service-account.json` (plus the second `weathergpt-4014b-firebase-adminsdk-*.json` key file) was never read, printed, logged, staged, or committed (gitignored); no live network I/O occurred in any non-opt-in test

## Self-Check: PASSED

- `backend/services/alert_watcher.py`, `backend/schemas/alerts.py`, `backend/tests/test_alert_watcher.py`, `backend/tests/test_fcm_secrets.py`, `backend/tests/test_live_fcm.py`, `.planning/phases/10-push-alerts/10-COVERAGE.md` all FOUND on disk; `backend/api/routes.py` and `backend/.env.example` modifications present
- Commits `fe9d094`, `edab2b4`, `829f816`, `b6a0cf9` verified present in `git log --all`
- Stub scan: no hardcoded empty values, placeholder text, or unwired data sources in plan files; all four routes wired to watcher plus fcm_client with throttle/sanitize
- Threat scan: new surfaces (four alert routes, watcher-to-provider seam, registry-to-status boundary) are the planned surfaces already covered by T-10-04 (suffix-only plus sentinel suite), T-10-05 (throttle plus skip-on-failure plus 18-city bound), T-10-06 (Orange-Red-only plus topic validation plus sanitized 502), T-10-07 accepted, T-10-SC (requirements SHA unchanged) — no new section needed
