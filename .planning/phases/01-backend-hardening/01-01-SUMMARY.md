# Phase 01 Plan 01: Tracer Slice + Tool Contract Summary

---
phase: 01-backend-hardening
plan: 01
type: execute
status: complete
tasks_completed: 2
tests: 4 passed (tests/test_chat_api.py: 2, tests/test_weather_tool.py: 2)
commits: 0 (git blocked by stale index.lock — best-effort commit failed, see below)
---

## Objective Achieved

Proved the thin end-to-end slice HTTP → route → agent → tool → response with a
green pytest run. Mocked `POST /api/chat` returns 200 with `reply` +
`alert_level`; `GET /health` returns the liveness shape; the mock tool contract
is frozen by tests. The async route no longer blocks the event loop
(`run_in_threadpool` around the sync `process_chat` call).

## Tasks Completed

### Task 1 (tracer): Mocked POST /api/chat end-to-end plus test scaffold — DONE
- `requirements.txt` carries version-floored `pytest>=8.0`,
  `pytest-asyncio>=0.23`, `httpx>=0.27` (official PyPI names only; installed
  successfully via `pip install -r requirements.txt`, which also pulled the
  declared langchain stack).
- `pytest.ini` at repo root: `asyncio_mode = auto`, `testpaths = tests`.
- `tests/conftest.py`: repo-root `sys.path` insert + autouse fixture forcing
  `OPENROUTER_API_KEY=test-dummy-key`, clearing `get_settings` cache and the
  agent executor cache before and after each test.
- `api/routes.py`: `await run_in_threadpool(process_chat,
  message=..., location=...)` with all three `except` branches unchanged
  (ValueError→422, RuntimeError→502, catch-all→500).
- `tests/test_chat_api.py`: httpx `AsyncClient` over `ASGITransport` bound to
  the `main` app; patches `process_chat` in the `api.routes` namespace;
  asserts 200 + mocked reply + `alert_level: Green` for "Hi in Mumbai";
  asserts `/health` returns `status: ok` plus `app` and `version` keys.
- Verify: `python -m pytest tests/test_chat_api.py -q` → **2 passed**.

### Task 2 (auto): Mock tool JSON contract test — DONE
- Created `tests/test_weather_tool.py` (new file, no existing files touched):
  invokes `get_current_weather` via `.invoke({"location": "Mumbai"})`, parses
  with `json.loads`, asserts `location` echo + `temperature_c`,
  `alert_level`, `source` keys; asserts tool name is `get_current_weather`.
- `tools/weather.py` untouched (signature frozen for Phase 2).
- Verify: `python -m pytest tests/ -q` → **4 passed**.

## Test Evidence

```
tests/test_chat_api.py ..   [ 50%]
tests/test_weather_tool.py .. [100%]
4 passed in 2.81s
```

Acceptance criteria met:
- POST /api/chat "Hi in Mumbai" (mocked) → 200, reply + alert_level Green ✔
- GET /health → 200, `{status: ok, app, version}` ✔
- `python -m pytest tests/ -q` exits 0, 0 failed ✔
- Mock tool returns parseable JSON with location / temperature_c / alert_level ✔

## Deviations from Plan

None in behavior. Execution note (not a deviation): most of Task 1's
artifacts (`requirements.txt` test deps, `pytest.ini`, `tests/conftest.py`,
`tests/test_chat_api.py`, threadpool offload in `api/routes.py`) were already
present on disk from a prior partial run and verified byte-for-byte against
the plan spec (seam namespace, cache resets, except-branch preservation) —
no edits were needed. Only `tests/test_weather_tool.py` was newly created by
this execution, plus `pip install -r requirements.txt` to provide the missing
langchain modules.

## Git Commits (best-effort — FAILED, non-blocking per instructions)

`git add` of the six plan files failed:
`fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists.`
(another process holds the repo lock; the lock was left untouched). No commits
exist yet (`main` has no commits). All file changes are on disk, verified by
the green pytest run above. Re-run `git add` + commit once the lock clears.

## Threat Register Notes

- T-01-SC: only the three official PyPI names installed, version-floored, no
  extra packages added — mitigated.
- T-01-01: conftest forces a dummy key; no real secret touched — mitigated.

## Self-Check: PASSED

- `requirements.txt`, `pytest.ini`, `tests/conftest.py`,
  `tests/test_chat_api.py`, `tests/test_weather_tool.py`, `api/routes.py`
  all present on disk with plan-specified content.
- Full suite green (4 passed) after `pip install -r requirements.txt`.
- No stubs introduced; no unrelated files modified.

## Next

Plan 01-02 (error contract tests) and 01-03 (observability, secrets) build on
this tracer. Suggested first action for 01-02: resolve the stale
`.git/index.lock` and commit this plan's files so the baseline is pinned.
