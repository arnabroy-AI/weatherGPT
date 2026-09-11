---
phase: 10-push-alerts
plan: 01
subsystem: push-notifications
tags: [fcm, httpx, mocktransport, oauth-seam, alerts]

# Dependency graph
requires:
  - phase: 09-multilingual-voice
    provides: [FCM_SERVICE_ACCOUNT_FILE setting, MockTransport test philosophy, sentinel-test pattern]
  - phase: 02-imd-live-data
    provides: [derive_alert_level sole threshold authority, set_transport pattern]
provides:
  - FCM v1 dispatch slice (token + topic) with injectable bearer seam
  - Mocked Orange-fixture dispatch proof with key-cleanliness sentinel
affects: [10-02 alert watcher and subscribe/dispatch routes, ship-gate FCM matrix]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 5860
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [token-provider seam over lazy google-auth opt-in, MockTransport URL/auth/body assertions]

key-files:
  created: [backend/services/fcm_client.py, backend/tests/test_fcm_dispatch.py]
  modified: []

key-decisions:
  - "Auth uses seam option b (injected bearer provider) with lazy google-auth opt-in — no new runtime deps"
  - "Topic validation strips an optional /topics/ prefix, then enforces the FCM topic charset"
  - "Empty-target validation runs before settings load so misuse fails fast without touching disk"

patterns-established:
  - "FCM Bearer seam: set_token_provider/reset_token_provider mirrors set_transport/reset_transport"
  - "Key-free logging: success lines carry only message name + target kind + alert level"
  - "Missing service-account file disables with 'not configured' RuntimeError, never a crash"

requirements-completed: [NOTF-01]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "FCM v1 token-path dispatch with Bearer auth returning the FCM message name"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_fcm_dispatch.py#test_token_path_dispatch"
        status: pass
    human_judgment: false
  - id: D2
    description: "FCM v1 topic-path dispatch with Bearer auth returning the FCM message name"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_fcm_dispatch.py#test_topic_path_dispatch"
        status: pass
    human_judgment: false
  - id: D3
    description: "Missing service-account file yields a clear disabled signal, no crash"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_fcm_dispatch.py#test_missing_file_disables_cleanly"
        status: pass
    human_judgment: false
  - id: D4
    description: "Forced-500 FCM outage leaks no private-key or bearer bytes into errors or logs"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_fcm_dispatch.py#test_forced_500_leaks_no_key_material"
        status: pass
    human_judgment: false

# Metrics
duration: 12min
completed: 2026-09-12
status: complete
---

# Phase 10 Plan 01: FCM Tracer Dispatch Summary

**Raw-httpx FCM v1 client with injectable bearer seam plus mocked Orange-fixture dispatch proof on token and topic paths**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-12T00:38:00+05:30
- **Completed:** 2026-09-12T00:50:00+05:30
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `backend/services/fcm_client.py` — FCM v1 send for token + topic targets with Bearer auth, service-account loader (None on missing file, sanitized errors on malformed JSON / missing fields), injectable token-provider seam, 10 s timeout, key-free logs
- `backend/tests/test_fcm_dispatch.py` — 7 tests: Orange authority pin, token-path dispatch, topic-path dispatch, missing-file skip, forced-500 sentinel cleanliness, empty-token ValueError, empty-topic ValueError
- Tracer proof: `pytest tests/test_fcm_dispatch.py -q` → 7 passed; full suite → 124 passed, 2 skipped (pre-existing live-test skips), no regressions
- Scope proof: `backend/requirements.txt` SHA256 unchanged (`00E5DF9B...C72925`) — zero new runtime deps

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer: FCM client with auth seam plus token and topic send** - `f7b89c8` (feat)
2. **Task 2: Dispatch proof: Orange fixture plus negative paths plus sentinel test** - `9486e4f` (test)

## Files Created/Modified

- `backend/services/fcm_client.py` - FCM v1 dispatch slice: `load_service_account`, `get_access_token`, `send_to_token`, `send_to_topic`, `set_transport`/`reset_transport`, `set_token_provider`/`reset_token_provider`
- `backend/tests/test_fcm_dispatch.py` - MockTransport dispatch proof with tmp_path fake service account and fake bearer seam

## Decisions Made

- Auth uses seam option b per plan (injected bearer provider; live `google-auth` stays a lazy opt-in import) — no new runtime deps, CI fully mocked
- Topic validation tolerates and strips a `/topics/` prefix, then enforces the FCM `[a-zA-Z0-9-_.~%]` charset with a 900-char bound; tokens capped at 4096 chars
- Empty-target `ValueError` validation runs before settings/disk access so misuse fails fast
- Success logs carry only message name + target kind + alert level (location deliberately excluded from logs; it travels in payload `data` only)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Commits on `main` follow this repo's established convention (prior phase commits `9c4f4ae`, `20a8d8a` also land directly on `main`; single checkout, no worktree in play).

## User Setup Required

None - no external service configuration required. Live FCM sends remain a documented opt-in (`pip install google-auth` + valid `FCM_SERVICE_ACCOUNT_FILE`); all tests are mocked.

## Tracer Feedback Gate

`gate="blocking-human"` is specified for tracer gates in the executor contract, but this plan's frontmatter declares `autonomous: true` with no `checkpoint:*` task, and the standing execution order for this run is to return `## EXECUTION COMPLETE` with pytest evidence. Auto-mode verification was therefore applied: the `<verify>` command (`pytest tests/test_fcm_dispatch.py -q`) was re-run end-to-end after both tasks and passes (7 passed), plus the full suite (124 passed, 2 pre-existing skips). No expansion tasks exist in this plan — plan 10-02 consumes this slice next.

## Next Phase Readiness

- Plan 10-02 (watcher + registry + routes) can build on `send_to_token` / `send_to_topic` directly; seams (`set_transport`, `set_token_provider`) are ready for its tests
- Real `backend/fcm-service-account.json` was never read, printed, logged, staged, or committed (gitignored, re-verified via `git check-ignore`); no live network I/O occurred in any test
- Watch item for 10-02: `backend/weathergpt-4014b-firebase-adminsdk-fbsvc-*.json` (second key file, also gitignored) was left untouched

## Self-Check: PASSED

- `backend/services/fcm_client.py` exists; `backend/tests/test_fcm_dispatch.py` exists
- Commits `f7b89c8` and `9486e4f` verified present in `git log --all`
- Stub scan: no hardcoded empty values, placeholder text, or unwired data sources in either file
- Threat scan: the only new network surface (FCM v1 send URL + Bearer header) is the planned surface already covered by T-10-01..T-10-03 mitigations; no new section needed

---
*Phase: 10-push-alerts*
*Completed: 2026-09-12*
