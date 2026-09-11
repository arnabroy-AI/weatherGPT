---
phase: 07-demo-hardening
plan: 01
subsystem: api
tags: [cors, rate-limit, stdlib, pytest, gitignore, demo]

# Dependency graph
requires:
  - phase: 06-frontend
    provides: [chat-contract test suite, frontend tsc gate]
provides:
  - ENV repair state on record (ENV-REPAIR-STATUS.md)
  - CORS env allowlist (open local-dev default, exact-match when set)
  - Stdlib per-IP throttle on POST /api/chat (429 + Retry-After)
  - Root .gitignore / .dockerignore secret hygiene + env examples
  - Hardening pytest suite (tests/test_demo_hardening.py)
affects: [07-demo-hardening plan 02 (compose, Dockerfiles, smoke test), demo readiness]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 4915    # chars/4 over touched files (whole-file for edited files; no git baseline exists for a true diff)
  tasks: 3        # tasks completed
  commits: 0      # MEASURED: git environmentally blocked (stale .git/index.lock + no initial commit); see Task Commits

# Tech tracking
tech-stack:
  added: []
  patterns: [stdlib-only sliding-window throttle, env-gated CORS allowlist, sanitize_detail on 429 bodies]

key-files:
  created: [.planning/phases/07-demo-hardening/ENV-REPAIR-STATUS.md, api/throttle.py, tests/test_demo_hardening.py, .gitignore, .dockerignore]
  modified: [core/config.py, main.py, api/routes.py, tests/conftest.py, .env.example]

key-decisions:
  - "No lock deletion attempted: workspace H:/ no-delete policy plus RX,W-only ACL outranks the plan's one-deletion allowance"
  - "Throttle limit read lazily from settings per call so monkeypatch + cache_clear changes behavior without app reload"
  - "CORS credentials enabled only for the explicit allowlist, never for star-open"
  - "Plan's literal tsc invocation run from frontend cwd (npx --prefix resolves packages but not tsconfig cwd)"

patterns-established:
  - "Throttle pattern: time.monotonic + threading.Lock sliding window keyed on request.client.host only"
  - "CORS pattern: get_cors_allow_origins() returns ['*'] when env unset, stripped exact-match list when set"
  - "429 pattern: HTTPException 429 with Retry-After header, detail passed through sanitize_detail"

requirements-completed: [DEMO-01]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Env-repair state probed and recorded (docker daemon, compose, index.lock, .env ignore, write probe)"
    requirement: "DEMO-01"
    verification:
      - kind: other
        ref: ".planning/phases/07-demo-hardening/ENV-REPAIR-STATUS.md (probe table + human follow-ups)"
        status: pass
    human_judgment: false
  - id: D2
    description: "CORS env allowlist live: star-open by default, exact-match list with credentials when set"
    requirement: "DEMO-01"
    verification:
      - kind: unit
        ref: "tests/test_demo_hardening.py#test_cors_star_open_when_allowlist_unset"
        status: pass
      - kind: unit
        ref: "tests/test_demo_hardening.py#test_cors_reflects_explicit_origin_allowlist"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per-IP throttle on POST /api/chat: over-limit returns 429 JSON with Retry-After, normal use unaffected"
    requirement: "DEMO-01"
    verification:
      - kind: unit
        ref: "tests/test_demo_hardening.py#test_chat_throttle_returns_429_with_retry_after"
        status: pass
      - kind: unit
        ref: "tests/test_demo_hardening.py#test_chat_single_post_still_succeeds"
        status: pass
    human_judgment: false
  - id: D4
    description: "Secret safety: 429/CORS bodies and logs carry no key material; root .env gitignored and docker-ignored"
    requirement: "DEMO-01"
    verification:
      - kind: unit
        ref: "tests/test_demo_hardening.py#test_throttle_and_cors_bodies_carry_no_key_material"
        status: pass
      - kind: other
        ref: "git check-ignore -q .env (exit 0) and .env absent from git status"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full backend suite plus frontend tsc and chat-contract gates green"
    requirement: "DEMO-01"
    verification:
      - kind: unit
        ref: "python -m pytest tests/ -q (81 passed, 1 skipped)"
        status: pass
      - kind: other
        ref: "npx tsc --noEmit from frontend cwd (exit 0)"
        status: pass
      - kind: unit
        ref: "node --test frontend/lib/__tests__/chat-contract.test.mjs (21 pass, 0 fail)"
        status: pass
    human_judgment: false

# Metrics
duration: ~25min
completed: 2026-09-11
status: complete
---

# Phase 7 Plan 01: Demo Hardening Tracer Summary

**Env-repair state on record plus stdlib CORS allowlist and per-IP chat throttle (429 + Retry-After) behind env vars, with ignore hygiene, all locked by 5 hardening tests and green backend/frontend gates**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-11T15:21:27+05:30 (first probe timestamp)
- **Completed:** 2026-09-11T15:32:10+05:30
- **Tasks:** 3 / 3 complete
- **Files modified:** 10 (5 created, 5 edited in place)

## Accomplishments

- ENV-REPAIR-STATUS.md records all five probes: docker daemon DOWN (client v29.7.2 / compose v5.3.1 present), `.git/index.lock` PRESENT and not removed (no-delete policy), `.env` unignored at probe time, new-file write probe PASSED, plus 4 human follow-ups (Modify grant, lock deletion, Docker Desktop start, initial commit)
- CORS allowlist wired end to end: `CORS_ALLOW_ORIGINS` setting (default empty) + `get_cors_allow_origins()` helper in core/config.py; main.py CORSMiddleware uses the helper with `allow_credentials` true only for the explicit list (T-07-02)
- Stdlib-only `api/throttle.py` (time.monotonic + threading.Lock sliding window, 60 req / 60 s per client IP keyed on `request.client.host` only) enforced on POST /api/chat with 429 JSON + `Retry-After`, detail via `sanitize_detail` (T-07-01, T-07-03); `CHAT_THROTTLE_PER_MIN` env-overridable; `reset_rate_limiter` wired into conftest autouse fixture
- Root `.gitignore` (exact `.env` line) + root `.dockerignore` (`.env`, `.env.local`, node_modules, `__pycache__`, `.planning`, `.git`, caches) + `.env.example` extended with the two new vars (existing key lines untouched; frontend example untouched)
- Hardening suite (5 tests) plus full gates: `pytest tests/` 81 passed / 1 skipped, `tsc --noEmit` exit 0, chat-contract 21 pass / 0 fail

## Task Commits

Per-task atomic commits were **environmentally blocked, not skipped**: the stale
`.git/index.lock` (0 bytes, 2026-09-11 00:23:42) makes every index write fail
with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists`,
and the repo has zero commits on `main` (D-01 initial commit never made).
Lock removal was forbidden by the workspace H:/ no-delete rule. All work is on
disk, verified, and ready to stage once a human deletes the lock and grants Modify.

1. **Task 1: Tracer env-repair probe + CORS + throttle** — `UNCOMMITTED (blocked: index.lock)` — ENV-REPAIR-STATUS.md, config/main/throttle/routes/conftest/tracer tests
2. **Task 2: Ignore hygiene** — `UNCOMMITTED (blocked: index.lock)` — .gitignore, .dockerignore, .env.example
3. **Task 3: Hardening regression gate** — `UNCOMMITTED (blocked: index.lock)` — extended hardening tests (CORS pair + secret-safety)

**Plan metadata:** `UNCOMMITTED (blocked: index.lock)` (docs: this SUMMARY)

_Recovery for human: verify no git process is running, delete `.git/index.lock`,
then `git add` the 10 files listed under Files Created/Modified and commit per task._

## Files Created/Modified

- `.planning/phases/07-demo-hardening/ENV-REPAIR-STATUS.md` — CREATED: five-probe record + 4 human follow-ups (D-01)
- `api/throttle.py` — CREATED: stdlib sliding-window limiter (`check_rate_limit`, `reset_rate_limiter`)
- `tests/test_demo_hardening.py` — CREATED: 5 hardening tests (happy path, 429+Retry-After, CORS open, CORS allowlist, no-key-material)
- `.gitignore` — CREATED: `.env` exact line + pycache/pytest/frontend-build ignores
- `.dockerignore` — CREATED: `.env`, `.env.local`, node_modules, `__pycache__`, `.planning`, `.git`, caches
- `core/config.py` — MODIFIED: + `CORS_ALLOW_ORIGINS`, `CHAT_THROTTLE_PER_MIN`, `get_cors_allow_origins()` helper
- `main.py` — MODIFIED: CORSMiddleware reads helper; credentials only for explicit list; no hardcoded star-only line
- `api/routes.py` — MODIFIED: throttle gate on POST /api/chat → 429 + Retry-After via sanitize_detail
- `tests/conftest.py` — MODIFIED: autouse fixture resets throttle store per test
- `.env.example` — MODIFIED (in place): appended commented `CORS_ALLOW_ORIGINS=` + `CHAT_THROTTLE_PER_MIN=60`

## Decisions Made

- No index.lock deletion attempted: the H:/ no-delete instruction and the observed `RX,W`-only ACL outrank the plan's conditional one-deletion allowance; recorded as human follow-up instead.
- Throttle limit read lazily from `get_settings()` on every `check_rate_limit` call (not cached at import), so tests change behavior with monkeypatch + `cache_clear()` and no app reload is needed.
- CORS `allow_credentials` is `(_cors_allow_origins != ["*"])`: open local-dev sends no credentials; explicit allowlist does (T-07-02 mitigation).
- The plan's literal `npx --prefix frontend tsc --noEmit` was executed from the frontend cwd as `npx tsc --noEmit` (see Deviations); exit 0 either way for the type check itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] tsc invocation cwd**
- **Found during:** Task 3 (Hardening regression gate)
- **Issue:** The plan's literal `npx --prefix frontend tsc --noEmit` exits 1 printing tsc help: `--prefix` resolves where npx finds the package, but tsc still resolves `tsconfig.json` from the repo-root cwd, where none exists. Pre-existing invocation quirk, unrelated to this plan's changes (frontend untouched).
- **Fix:** Ran the identical type check with the frontend directory as cwd (`npx tsc --noEmit`): exit 0, no output. No plan or source file changed for this.
- **Files modified:** none
- **Verification:** `TSC-EXIT=0`; chat-contract gate independently green (21/0)
- **Committed in:** n/a (git blocked; documented under Task Commits)

---

**Total deviations:** 1 auto-fixed (1 blocking-invocation)
**Impact on plan:** No scope creep; the gate intent (frontend tsc clean) is proven. The plan text's literal command should be read as "frontend tsc clean" in Plan 02+.

## Issues Encountered

- **Git fully blocked by stale index.lock + zero-commit repo:** `git add` fails (`Unable to create index.lock: File exists`); `git log` confirms `main` has no commits. Both are the D-01 human prerequisites this plan was designed to surface, now recorded with recovery steps. No retries attempted per D-01.
- **Docker daemon down:** `docker info` server section fails on the Desktop npipe; compose client v5.3.1 present but unusable. Plan 02 (compose up / smoke test) needs Docker Desktop started — flagged as human follow-up.
- **`.env` with live keys sits untracked at repo root:** now neutralized going forward by the new `.gitignore` (proven: `.env` absent from `git status`, `check-ignore` exit 0, `.gitignore:2:.env`). The initial commit must still exclude it — human follow-up.

## Known Stubs

None. Scanned created/modified files for `=[]`/`={}`/`=null`/`TODO`/`FIXME`/`placeholder`/`coming soon`: the only `X-Forwarded-For` mention is the throttle docstring explicitly refusing to trust it (T-07-01 accepted limitation). No mock data flows to any UI.

## Threat Flags

None beyond the plan's `<threat_model>`: no new network endpoints, auth paths, or schema changes. The only new trust-boundary behavior (Origin parsing, per-IP counting, 429 bodies) maps to T-07-01 (accept, documented), T-07-02 (mitigate: exact-match list, credentials only for explicit list), T-07-03 (mitigate: 429 detail via `sanitize_detail`, dummy-key-absent test). Zero new dependencies (T-07-SC).

## User Setup Required

None - no external service configuration required. (Human prerequisites are
environment repairs, not service setup: see ENV-REPAIR-STATUS.md follow-ups —
Modify grant, index.lock deletion, Docker Desktop start, initial commit.)

## Next Phase Readiness

- Ready for Plan 02 (Dockerfiles, compose.yaml, README, demo smoke): CORS/throttle env vars are documented in `.env.example`; `.dockerignore` already excludes secrets and bulk.
- Blockers for Plan 02: Docker daemon must be started; git lock must be cleared so Plan 02 work can be committed. Neither is retryable by the agent.

---
*Phase: 07-demo-hardening*
*Completed: 2026-09-11*

## Self-Check: PASSED

- ENV-REPAIR-STATUS.md: FOUND; names daemon NO / compose YES / index.lock present-not-removed / .env ignored-after-task-2 / write probe YES
- core/config.py: FOUND `CORS_ALLOW_ORIGINS` + `CHAT_THROTTLE_PER_MIN` + `get_cors_allow_origins`
- main.py: FOUND `CORS_ALLOW_ORIGINS`; no `allow_origins=[` hardcoded star line
- api/throttle.py: FOUND `Retry-After` + `reset_rate_limiter`
- Single POST → 200 and over-limit POST → 429 + Retry-After: PROVEN (`2 passed` tracer run; `5 passed` extended run)
- `git check-ignore -q .env`: exit 0; `.env` absent from `git status`
- Gates: `pytest tests/` 81 passed / 1 skipped; `tsc --noEmit` exit 0; chat-contract 21 pass / 0 fail
- Commits: none possible (index.lock) — recorded as UNCOMMITTED/blocked, not narrated as done
