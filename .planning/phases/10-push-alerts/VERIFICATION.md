# Phase 10: Proactive push alerts — Verification Report

**Phase Goal:** Threshold watcher dispatches FCM push for Orange/Red alerts (ROADMAP.md Phase 10)
**Verified:** 2026-09-12 (UTC)
**Status:** passed
**Score:** 3/3 success criteria verified
**Mode:** Initial verification (no prior VERIFICATION.md; goal-backward from ROADMAP + CONTEXT + PLANs)

## Goal Achievement

### Observable Truths (the 3 ROADMAP success criteria)

| # | Truth (ROADMAP Phase 10 SC) | Status | Evidence |
|---|-----------------------------|--------|----------|
| 1 | Orange/Red condition triggers an FCM dispatch (topic + token paths) with key-free logs; unit-proven with mocked FCM endpoint | ✓ VERIFIED | `backend/services/fcm_client.py` `send_to_token` + `send_to_topic` POST to `https://fcm.googleapis.com/v1/projects/{project_id}/messages:send` with `Authorization: Bearer` header, return the FCM `name`. Verifier ran `python -m pytest tests/test_fcm_dispatch.py -q` in `backend/`: **7 passed**. MockTransport handler asserts URL path `/v1/projects/test-project-123/messages:send`, Bearer `fake-access-token-9z`, `message.token` / `message.topic` bodies, `data.alert_level == Orange`. Forced-500 sentinel test asserts fake private key + fake bearer absent from raised error + caplog. Success log carries only `name + target + alert_level`. |
| 2 | Watcher runs on schedule, dedupes repeat alerts, never storms; pytest green | ✓ VERIFIED | `backend/services/alert_watcher.py`: `WATCH_CITIES` derived from `CITY_COORDS` (18 entries, pinned by test), `DISPATCH_LEVELS = {Orange, Red}`, `COOLDOWN_S = 21600` (6h). `should_dispatch` on monotonic time: first Orange fires, repeat inside 6h suppressed, Orange→Red upgrade re-fires immediately, Green/Yellow never fire, Red→Orange downgrade suppressed, locations independent. `run_watch_cycle` returns `{checked: 18, dispatched, skipped}`, rolls back dedup record on send failure, never raises on single-city failure. Schedule semantic = callable `run_watch_cycle` + `POST /api/alerts/check` as documented hourly cron target (planner's recorded CONTEXT-discretion decision: no in-process scheduler, stdlib-only). Verifier ran `python -m pytest tests/test_alert_watcher.py -q`: **23 passed** (dedup matrix 6 tests, cached-seam single-hit Orange, cycle 18-then-0, Green-cycle 0 sends, failure isolation, 8 route tests). |
| 3 | No secrets in code/logs; service-account file gitignored and validated at startup | ✓ VERIFIED | `.gitignore` lines 4–5: `fcm-service-account.json`, `*-firebase-adminsdk-*.json` — `git check-ignore -v` confirms both key files ignored; `git ls-files` shows neither tracked. `load_service_account` returns `None` on missing file (clean disable, "not configured" RuntimeError on send), raises sanitized RuntimeError on malformed JSON / missing fields, never echoes contents. `backend/requirements.txt` has no `google-auth`/`firebase`/`fcm` (zero new runtime deps; live auth is a lazy opt-in import). `backend/.env.example` documents `FCM_SERVICE_ACCOUNT_FILE=fcm-service-account.json` with missing-file-disables comment. `backend/core/config.py` carries the `FCM_SERVICE_ACCOUNT_FILE` setting. Sentinel suite `test_fcm_secrets.py` (3 unique sentinels: private key, access token, device token) clean across direct-500, send-route 502, check/status routes + `sanitize_detail` unit check. Verifier ran `python -m pytest tests/ -q`: **151 passed, 3 skipped** (2 pre-existing live + 1 live-FCM opt-in). |

**Score:** 3/3 truths verified (0 present-but-unverified, 0 failed)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/services/fcm_client.py` | FCM v1 token+topic send, auth seam, key-free logs | ✓ VERIFIED | Exists (347 lines), substantive: `load_service_account`, `get_access_token`, `send_to_token`, `send_to_topic`, `set_transport`/`reset_transport`, `set_token_provider`/`reset_token_provider`, 10s timeout, ValueError on empty token/topic, sanitized RuntimeError with status code only. Wired: imported by `alert_watcher._default_send` and `api/routes.py` alerts_send. |
| `backend/services/alert_watcher.py` | Registry + cached-seam evaluate + 6h dedup + 18-city cycle | ✓ VERIFIED | Exists (378 lines), substantive: lock-guarded `_tokens`/`_topic_subs`, `evaluate_city` via `get_current_weather.invoke` JSON parse (no second heuristic), monotonic `should_dispatch` with upgrade bypass, `run_watch_cycle(send_fn, now)` with rollback-on-failure. Wired: called by all 4 alert routes; `reset_for_tests` used by test fixtures. |
| `backend/schemas/alerts.py` | Subscribe/Send/Check/Status shapes with caps | ✓ VERIFIED | Exists (91 lines): SubscribeRequest (token 2048, topics ≤32), SendRequest (exactly-one-target, title 200, body 1000, location 120), CheckResponse, StatusResponse. Wired: route handler signatures. |
| `backend/api/routes.py` (alert routes) | subscribe/send/check/status with throttle + sanitize + 422/502 | ✓ VERIFIED | 4 routes present (`/alerts/subscribe`, `/alerts/send`, `/alerts/check`, `/alerts/status`), all behind `_check_alerts_throttle` + `sanitize_detail` + ValueError→422 / RuntimeError→502 / catch-all 500. Send enforces Orange-Red-only 422 before touching disk/network; subscribe/status echo at most token last-6 + counts. |
| `backend/tests/test_fcm_dispatch.py` | Tracer + sentinel proof (≥6 tests) | ✓ VERIFIED | 7 tests, all pass (verifier-ran). |
| `backend/tests/test_alert_watcher.py` | Dedup matrix + cached seam + routes | ✓ VERIFIED | 23 tests, all pass (verifier-ran). |
| `backend/tests/test_fcm_secrets.py` | Three-sentinel errors/bodies/logs suite | ✓ VERIFIED | 4 tests, all pass (verifier-ran). |
| `backend/tests/test_live_fcm.py` | Skipped-by-default live opt-in | ✓ VERIFIED | `skipif RUN_LIVE_FCM != 1`, `validate_only: true` benign Orange topic payload, skipped in full run. |
| `.planning/phases/10-push-alerts/10-COVERAGE.md` | FCM matrix: INTEGRATE token/topic/eval + SMS/WhatsApp OPT-OUT | ✓ VERIFIED | 3 INTEGRATE rows tagged NOTF-01/NOTF-01/NOTF-02 + exactly the SMS/WhatsApp OPT-OUT row with no-credentials-plus-DLT reason + notes (6h/upgrade, google-auth opt-in, validate_only, key posture). |
| `backend/.env.example` | FCM_SERVICE_ACCOUNT_FILE doc line | ✓ VERIFIED | Line 18 + missing-file-disables comment. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fcm_client` token-provider seam | Outbound `Authorization: Bearer` header | `get_access_token` → `_send_message` headers | ✓ WIRED | Test asserts `request.headers["authorization"] == "Bearer fake-access-token-9z"` on both paths. |
| Service-account `project_id` | FCM v1 send URL | `FCM_SEND_URL_TEMPLATE.format(project_id=…)` | ✓ WIRED | Test asserts request path `/v1/projects/test-project-123/messages:send`. |
| Watcher `alert_level` | Tool payload from `derive_alert_level` | `evaluate_city` reads `get_current_weather` JSON `alert_level`/`advisory`/`location` directly | ✓ WIRED | `test_no_second_heuristic_in_watcher` (no import/call/redefinition of `derive_alert_level` in watcher source) + `test_evaluate_city_orange_via_cached_seam_single_hit` (code-95 provider JSON → Orange, 1 upstream hit across 2 calls via tool cache). `test_orange_authority_pin` pins `derive_alert_level(95) == "Orange"`. |
| Routes | Watcher + fcm_client | `alerts_subscribe/send/check/status` handlers | ✓ WIRED | Behind per-IP throttle + sanitize; 8 route tests green. |
| Watcher fan-out | Topic + subscribed tokens | `_default_send`: topic send must succeed, per-token sends best-effort | ✓ WIRED | Code + check-route outage test (200 with clean bodies/logs against 500 FCM). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `fcm_client._send_message` | `name` | FCM v1 `messages:send` response JSON `name` field (mocked in CI) | ✓ | ✓ FLOWING (missing-name → sanitized RuntimeError) |
| `alert_watcher.evaluate_city` | `alert_level`/`advisory`/`location` | `get_current_weather` tool JSON string (cached seam over provider) | ✓ | ✓ FLOWING (single upstream hit proven; failure → None, never raise) |
| `alerts/status` | counts + `fcm_configured` | Live registry counts + `load_service_account() is not None` probe | ✓ | ✓ FLOWING (zero token bytes; test asserts token absent from body + logs) |

### Behavioral Spot-Checks (verifier-ran, `backend/` cwd)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Orange/Red FCM dispatch both paths, key-free | `python -m pytest tests/test_fcm_dispatch.py -q` | 7 passed in ~13s | ✓ PASS |
| Watcher dedup + cached seam + routes | `python -m pytest tests/test_alert_watcher.py -q` | 23 passed in ~21s | ✓ PASS |
| Sentinel secrets suite | `python -m pytest tests/test_fcm_secrets.py -q` | 4 passed in ~18s | ✓ PASS |
| Full gates green, live safely skipped | `python -m pytest tests/ -q` | 151 passed, 3 skipped in ~30s | ✓ PASS |

### Extra Contract Checks (from the verification request)

| Check | Result | Status |
|-------|--------|--------|
| `derive_alert_level` sole authority | Watcher never imports/calls/redefines it; dispatch tests pin code 95 → Orange; evaluation flows through the cached tool seam | ✓ VERIFIED |
| Service account never touched by tests | Only a docstring mention of `backend/fcm-service-account.json` in `test_fcm_dispatch.py`; all tests use `tmp_path` fake SA + `FCM_SERVICE_ACCOUNT_FILE` repoint + `cache_clear` | ✓ VERIFIED |
| No live network in CI | 12 `MockTransport` uses across the three test files; ASGITransport for route tests; only raw `httpx.Client` is inside the `RUN_LIVE_FCM=1`-gated skipped test | ✓ VERIFIED |
| Green/Yellow never push | `DISPATCH_LEVELS = {Orange, Red}` + `should_dispatch` early-False + `run_watch_cycle` `below_threshold` skip + send-route 422 ("Only Orange and Red alerts may be pushed") before service-account load; covered by `test_dedup_matrix_green_yellow_never_fire`, `test_run_watch_cycle_green_dispatches_nothing`, `test_route_send_green_422` | ✓ VERIFIED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NOTF-01 | 10-01, 10-02 | FCM push dispatch for Orange/Red (service-account auth, topic + token, key-free logs) | ✓ SATISFIED | `fcm_client.py` + 7 dispatch tests + 8 route tests + 4 sentinel tests, all verifier-ran green |
| NOTF-02 | 10-02 | Threshold watcher on schedule, no duplicate storms | ✓ SATISFIED | `alert_watcher.py` 18-city cycle + full dedup matrix + `checked: 18` route proof, all verifier-ran green |

No orphaned requirements: only NOTF-01/NOTF-02 map to Phase 10, both claimed by the plans.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `services/fcm_client.py`, `services/alert_watcher.py`, `schemas/alerts.py`, `api/routes.py` | Scan for TODO/FIXME/XXX/TBD/placeholder/stub-return/console.log | — | None found: clean |

Commits present: `f7b89c8`, `9486e4f` (plan 01), `fe9d094`, `b6a0cf9`, `edab2b4`, `829f816`, `5966018` (plan 02).

### Human Verification Required

None. All three success criteria are programmatically verifiable and were verified by running the tests. The only live path (real FCM send) is an intentional `RUN_LIVE_FCM=1` + `google-auth` + real-key opt-in, skipped by default — running it requires human credentials and is out of scope for CI verification.

### Gaps Summary

No gaps. Phase goal achieved: the threshold watcher dispatches FCM push for Orange/Red alerts with 6h dedup and upgrade re-fire, secrets stay out of code/logs, and the full suite is green.

---
_Verified: 2026-09-12_
_Verifier: the agent (gsd-verifier)_
