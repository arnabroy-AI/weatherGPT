# Phase 01 Plan 02: Error Contract + Agent Retry Summary

---
phase: 01-backend-hardening
plan: 02
type: execute
status: complete
tasks_completed: 3
tests: 6 passed (tests/test_error_contract.py) + full suite 18 passed, 1 skipped
commits: 0 (git blocked by stale index.lock — best-effort commits failed, see below)
---

## Objective Achieved

Proved every sad path the ROADMAP success criteria demand. The agent layer
bounds each LLM call at 30s with exactly one retry then raises loudly
(D-11/D-06); every route error detail is sanitized of key material (D-17)
with full tracebacks logged server-side (D-07); the 422/502/500 mapping is
unchanged (D-05); schema limits reject bad payloads while padded-valid input
still passes (D-15). No degraded-200 fallback, no new status codes.

## Tasks Completed

### Task 1 (auto): Agent LLM timeout plus single retry — DONE
- `services/agent.py`: added `LLM_REQUEST_TIMEOUT_SECONDS = 30` and
  `LLM_MAX_ATTEMPTS = 2` module constants; `request_timeout=30` passed to
  `ChatOpenAI` in `_build_llm`; `process_chat` wraps `executor.invoke` in a
  two-iteration loop that returns on success, `logger.exception`s each
  failure server-side, and raises `RuntimeError` with the existing
  `WeatherGPT agent invocation failed` prefix after exhaustion.
- `_derive_alert_level`, system prompt, tool list, cache helpers untouched.
- Verify: `python -m pytest tests/test_chat_api.py tests/test_weather_tool.py -q`
  → **4 passed**.

### Task 2 (auto): Route error responses, sanitize plus tracebacks — DONE
- `api/routes.py`: added `sanitize_detail()` (replaces both configured key
  values with `[REDACTED]`, reads `get_settings()` lazily inside the call so
  tests can monkeypatch keys, skips empty values); consulted on all three
  error branches; `logger.exception` with request path in each branch;
  mapping unchanged (ValueError→422, RuntimeError→502, catch-all→generic
  fixed `"Unexpected error: request failed."` 500 with no interpolation).
- Threadpool call from 01-01 untouched; only additive change to the handler
  signature is an injected `Request` (no client-visible change).
- Verify: tracer + tool tests → **4 passed**.

### Task 3 (auto): Error-contract and validation tests — DONE
- Created `tests/test_error_contract.py` (new file, 6 tests, LLM kept out):
  missing-key 502 via the real `process_chat` path; LLM-outage 502 via a
  stubbed executor (also asserts exactly 2 invoke calls = 1 retry, and
  never-200); generic-500 via route-namespace patch asserting the fixed
  `Unexpected error` prefix and no internal state leak; 422s for empty,
  2001-char, and 121-char-location payloads; padded-valid message still 200;
  direct `sanitize_detail` redaction test (D-17); every error body asserted
  free of tracebacks, frame markers, module-path exceptions, and key values.
- Verify: `python -m pytest tests/test_error_contract.py -q` → **6 passed**;
  full `python -m pytest tests/ -q` → **18 passed, 1 skipped** (skip is the
  pre-existing opt-in live OpenRouter test; concurrent plan 01-03's
  observability/secrets tests also green against these changes).

## Test Evidence

```
tests/test_error_contract.py ......   [100%]
6 passed in 3.69s
tests/ : 18 passed, 1 skipped in 6.12s
```

Acceptance criteria met:
- Missing key → 502 with safe detail, no traceback leak ✔
- Forced LLM failure → retried once, then honest 502 with
  invocation-failed prefix, never 200 ✔
- Generic failure → 500 with fixed Unexpected prefix ✔
- Empty / 2001-char / 121-char-location → 422; padded-valid → 200 ✔

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing-key test used empty-string instead of delenv**
- **Found during:** Task 3 (first run: 1 failed, 5 passed)
- **Issue:** `monkeypatch.delenv("OPENROUTER_API_KEY")` fell through to the
  repo `.env` file's real key (pydantic `env_file`), causing a REAL network
  call to OpenRouter (401) instead of `validate_secrets` firing.
- **Fix:** `monkeypatch.setenv("OPENROUTER_API_KEY", "")` — empty is falsy,
  so `validate_secrets` raises before any network; suite runs offline in ~3.7s.
- **Files modified:** tests/test_error_contract.py
- **Commit:** uncommitted (git blocked, see below)

## Git Commits (best-effort — FAILED, non-blocking per instructions)

All three `git add` + `git commit` attempts failed:
`fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists.`
(lock held by another process; left untouched). `main` still has no commits;
all changes are on disk and proven by the green runs above. Re-run `git add`
+ commit once the lock clears. Files changed by this plan only:
`services/agent.py`, `api/routes.py`, `tests/test_error_contract.py` (new).

## Threat Register Notes

- T-02-01 (info disclosure in error details): sanitize helper on every
  branch + direct redaction test + leak assertions on all bodies — mitigated.
- T-02-02 (hung upstream holds worker): 30s bound + exactly-once retry then
  loud 502; retry count asserted in test — mitigated.
- T-02-03 (prompt injection): accepted per D-15, length limits only — no work.

## Self-Check: PASSED

- `services/agent.py` carries both constants, `request_timeout`, retry loop.
- `api/routes.py` carries `sanitize_detail`, three `logger.exception` calls,
  unchanged 422/502/500 codes.
- `tests/test_error_contract.py` present with 6 tests, all green; full suite
  18 passed / 1 skipped (pre-existing live-test skip).
- No files outside this plan's `files_modified` touched; no stubs introduced.

## Next

Plan 01-03 (observability/secrets) already has passing tests on disk against
these changes. Suggested first action: clear the stale `.git/index.lock` and
commit Wave 1 + Wave 2 files so the hardened baseline is pinned.
