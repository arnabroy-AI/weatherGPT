---
phase: 07-demo-hardening
plan: 02
subsystem: demo
tags: [docker, compose, readme, smoke, seeded-queries, demo]

# Dependency graph
requires:
  - phase: 07-demo-hardening
    provides: [CORS allowlist, per-IP chat throttle, ignore hygiene, ENV-REPAIR-STATUS]
provides:
  - Backend Dockerfile (pinned python:3.12-slim-bookworm, uvicorn)
  - Frontend Dockerfile (multi-stage node:20-alpine, standalone runner)
  - Standalone Next output (frontend/next.config.mjs)
  - Root compose.yaml pair (runtime-only keys via host .env)
  - README 10-minute SIH judge flow
  - Offline-capable seeded smoke script (scripts/demo_smoke.py + --live opt-in)
affects: [demo readiness, SIH judging, phase 8+ (v2 scope untouched)]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 3433    # chars/4 over touched files (13730 bytes across 6 files)
  tasks: 3        # tasks completed
  commits: 0      # MEASURED: git environmentally blocked (stale .git/index.lock persists); see Task Commits

# Tech tracking
tech-stack:
  added: []
  patterns: [build-arg-only public URL bake, env_file runtime-only keys, stdlib-only smoke checks]

key-files:
  created: [Dockerfile, frontend/Dockerfile, compose.yaml, README.md, scripts/demo_smoke.py]
  modified: [frontend/next.config.mjs]

key-decisions:
  - "Runner stage omits public/ copy: frontend has no public dir, so COPY would fail the build"
  - "Smoke script carries no secret-marker literals: secret-freedom of compose.yaml is proven by grep evidence, not embedded patterns"
  - "tsc run from frontend cwd (npx tsc --noEmit), same as Plan 01: --prefix resolves packages but not tsconfig cwd"

patterns-established:
  - "Compose pattern: backend env_file .env + frontend build-arg public URL, exactly two services, depends_on backend"
  - "Smoke pattern: stdlib-only parity (README x starters x teaser byte-match) + minimal indent-aware compose parse + optional health probe"

requirements-completed: [DEMO-01, DEMO-02]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Backend + frontend images defined on pinned bases, keys unbaked, standalone output"
    requirement: "DEMO-02"
    verification:
      - kind: other
        ref: "Dockerfile (FROM python:3.12-slim-bookworm, uvicorn main:app, zero ENV OPENROUTER/WEATHER lines)"
        status: pass
      - kind: other
        ref: "frontend/Dockerfile (ARG NEXT_PUBLIC_WEATHERGPT_API, node:20-alpine x3, node server.js)"
        status: pass
      - kind: other
        ref: "frontend/next.config.mjs (output standalone) + npx tsc --noEmit exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Compose pair validates from disk, keys runtime-only via host .env"
    requirement: "DEMO-02"
    verification:
      - kind: other
        ref: "docker compose config --quiet (exit 0, no daemon needed)"
        status: pass
      - kind: other
        ref: "compose.yaml content gates (backend+frontend, env_file .env, build-arg URL, ports 8000/3000, zero secret markers)"
        status: pass
    human_judgment: false
  - id: D3
    description: "README 10-minute flow plus offline smoke parity over the seeded trio"
    requirement: "DEMO-01"
    verification:
      - kind: other
        ref: "README.md content gates (compose up, both localhost ports, 10 min, trio exact, OPENROUTER_API_KEY, offline/live note)"
        status: pass
      - kind: other
        ref: "python scripts/demo_smoke.py --offline (exit 0, parity PASS, compose PASS)"
        status: pass
      - kind: unit
        ref: "python -m pytest tests/ -q (81 passed, 1 skipped)"
        status: pass
    human_judgment: false

# Metrics
duration: ~30min
completed: 2026-09-11
status: complete
---

# Phase 7 Plan 02: Dockerfiles + Compose Pair + README + Smoke Summary

**One-command SIH demo defined: pinned backend + standalone-frontend images, runtime-only keys via host .env, README clone-to-chat flow, and an offline-capable seeded-trio smoke script — all gates green, live `compose up` left as the single human follow-up (daemon down)**

## Performance

- **Duration:** ~30 min
- **Tasks:** 3 / 3 complete
- **Files modified:** 6 (5 created, 1 edited in place)

## Accomplishments

- Backend `Dockerfile`: `FROM python:3.12-slim-bookworm`, requirements-first layer cache, sources-only copy (`main.py api core schemas services tools`), `EXPOSE 8000`, `uvicorn main:app --host 0.0.0.0 --port 8000`, zero `ENV OPENROUTER/WEATHER` lines (T-07-04)
- Frontend `Dockerfile`: three-stage `node:20-alpine` (`deps` npm ci, `builder` with `ARG NEXT_PUBLIC_WEATHERGPT_API` default `http://localhost:8000` promoted to `ENV` for the public-inline bake, `runner` with standalone server + static assets, `node server.js`); `frontend/next.config.mjs` gains `output: "standalone"` and nothing else
- Root `compose.yaml`: exactly two services — backend (builds root Dockerfile, `env_file: .env`, `8000:8000`) + frontend (builds `frontend/Dockerfile` with `NEXT_PUBLIC_WEATHERGPT_API` build arg, `3000:3000`, `depends_on: backend`); no secret values inline; `docker compose config --quiet` exits 0 without a daemon
- `README.md`: prerequisites (Docker, 10 minutes), compose-primary quick start (clone, `cp .env.example .env`, fill `OPENROUTER_API_KEY`, `docker compose up --build`, open http://localhost:3000), local-dev secondary (`uvicorn main:app` + `NEXT_PUBLIC_WEATHERGPT_API=... npm run dev`), the three seeded queries byte-matching `STARTER_QUERIES`, Green-to-Red badge note, live-key-vs-offline note, troubleshooting (daemon down, port busy, `index.lock` → ENV-REPAIR-STATUS.md), English-text-chat-only scope note
- `scripts/demo_smoke.py` (stdlib only): default offline mode asserts README × `starters.tsx` × `live-demo-teaser.tsx` byte-parity for the trio, parses `compose.yaml` with exactly `{backend, frontend}` plus `env_file`/build-arg presence, probes `GET /health` as optional; `--live` posts the trio to a running backend with per-query PASS/FAIL; never reads `.env`, never prints key values

## Task Commits

Per-task atomic commits were **environmentally blocked, not skipped**: the stale
`.git/index.lock` persists (deletion forbidden by the H:/ no-delete policy) so
`git add` fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock':
File exists`, and the repo still has zero commits on `main`. All work is on
disk, verified, and ready to stage once a human deletes the lock and grants Modify.
`git status` confirms `.env` stays untracked/ignored (`git check-ignore -q .env`
exit 0) — it was never staged.

1. **Task 1: Dockerfiles plus standalone frontend output** — `UNCOMMITTED (blocked: index.lock)` — Dockerfile, frontend/Dockerfile, frontend/next.config.mjs
2. **Task 2: Compose pair with runtime-only keys plus config validation** — `UNCOMMITTED (blocked: index.lock)` — compose.yaml
3. **Task 3: README 10-minute flow plus offline-capable seeded smoke script** — `UNCOMMITTED (blocked: index.lock)` — README.md, scripts/demo_smoke.py

**Plan metadata:** `UNCOMMITTED (blocked: index.lock)` (docs: this SUMMARY)

_Recovery for human: verify no git process is running, delete `.git/index.lock`,
then `git add Dockerfile frontend/Dockerfile frontend/next.config.mjs compose.yaml
README.md scripts/demo_smoke.py .planning/phases/07-demo-hardening/07-02-SUMMARY.md`
(excluding `.env`) and commit per task._

## Files Created/Modified

- `Dockerfile` — CREATED: pinned backend image, sources-only copy, uvicorn CMD, no secret ENV
- `frontend/Dockerfile` — CREATED: multi-stage standalone runner, public-URL build arg only
- `compose.yaml` — CREATED: backend + frontend pair, `env_file: .env`, ports 8000/3000
- `README.md` — CREATED: 10-minute judge flow, seeded trio, offline/live note, troubleshooting
- `scripts/demo_smoke.py` — CREATED: offline parity + compose parse + optional health, `--live` opt-in
- `frontend/next.config.mjs` — MODIFIED (in place): + `output: "standalone"` only

## Decisions Made

- Runner stage omits the `public/` copy: `frontend/` has no `public` directory, so `COPY --from=builder /app/public` would fail the build. Re-add it if a `public/` dir appears later.
- Smoke script carries no secret-marker string literals: an earlier draft scanned compose.yaml for `sk-or`/`your-key-here` markers, which embeds key-like substrings in a new file and trips mechanical no-key-material greps. Secret-freedom of `compose.yaml` is instead proven by grep evidence (`ALL-NEW-FILES-KEY-FREE-OK`); the script keeps structural checks only, exactly per plan.
- `tsc` run from the frontend cwd (`npx tsc --noEmit`, exit 0) rather than the plan's literal `npx --prefix frontend tsc --noEmit`, same deviation as Plan 01: `--prefix` resolves the package but tsc still resolves `tsconfig.json` from the repo-root cwd.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] tsc invocation cwd**
- **Found during:** Task 1 (Dockerfiles plus standalone frontend output)
- **Issue:** The plan's literal `npx --prefix frontend tsc --noEmit` resolves tsc from the frontend package but resolves `tsconfig.json` from the repo root, where none exists (same pre-existing quirk documented in 07-01-SUMMARY). No frontend source changed for this.
- **Fix:** Ran the identical type check with the frontend directory as cwd (`npx tsc --noEmit`): exit 0, no output.
- **Files modified:** none
- **Commit:** n/a (git blocked; documented under Task Commits)

**2. [Rule 2 - Missing critical] Smoke-script secret-marker literals removed**
- **Found during:** Task 3 verification (no-key-material grep over new files)
- **Issue:** Draft `check_compose()` embedded the literals `sk-or` / `your-key-here` as scan markers — functionally a detector, but indistinguishable from baked key material to any grep-based gate and contrary to the T-07-04/T-07-05 zero-key-material bar for new files.
- **Fix:** Removed the marker loop; the script keeps the plan-specified checks (byte-parity, two-service parse, optional health, `--live`). Compose secret-freedom is proven by out-of-band grep instead.
- **Files modified:** scripts/demo_smoke.py
- **Verification:** `ALL-NEW-FILES-KEY-FREE-OK`; `python scripts/demo_smoke.py --offline` re-run exits 0
- **Commit:** n/a (git blocked; documented under Task Commits)

---

**Total deviations:** 2 auto-fixed (1 blocking-invocation, 1 missing-critical)
**Impact on plan:** No scope creep; both keep the plan's intent while holding the key-hygiene bar. No architectural changes (no Rule 4).

## Issues Encountered

- **Git fully blocked (unchanged from Plan 01):** stale `.git/index.lock` + zero-commit `main`. `git add` fails; `git status` (read-only) works and proves `.env` ignored. Human follow-ups from ENV-REPAIR-STATUS.md still stand (Modify grant, lock deletion, initial commit).
- **Docker daemon down (unchanged from Plan 01):** `docker compose config --quiet` validates client-side (exit 0), but a live `docker compose up` run was impossible. Recorded as human follow-up, not retried (per environment notes: do not hang waiting for a daemon).

## Known Stubs

None. Scanned created/modified files for `=[]`/`={}`/`=null`/`TODO`/`FIXME`/`placeholder`/`coming soon`/empty handlers: no hits. The smoke `--live` path is fully wired (real POSTs, per-query verdicts), not a stub — it simply needs a running backend plus real keys.

## Threat Flags

None beyond the plan's `<threat_model>`: no new network endpoints, auth paths, or schema changes. New-file surface maps to T-07-04 (mitigate: Dockerfiles/compose carry zero secret values — grep-proven), T-07-05 (mitigate: smoke script never reads `.env`/env keys and never prints key-adjacent values — `SMOKE-NO-KEY-PRINT-OK`, `SMOKE-NO-ENV-READ-OK`), T-07-06 (mitigate: compose inherits Plan 01 throttle, unchanged), T-07-SC (mitigate: pinned `python:3.12-slim-bookworm` + `node:20-alpine` — human verifies tags on Docker Hub at review).

## User Setup Required

None for the artifacts as authored. Human follow-ups (environment repairs, not service setup):

1. **Start Docker Desktop**, then run the live proof: `docker compose up --build`, open http://localhost:3000, send the three seeded queries, optionally `python scripts/demo_smoke.py --live`.
2. **Git repairs** (see Task Commits recovery): delete `.git/index.lock` (no git running), grant Modify, initial commit excluding `.env`.

## Next Phase Readiness

- Demo hardening artifacts complete: Plan 01 (CORS/throttle/ignores) + Plan 02 (images/compose/README/smoke). Remaining demo work is human-side: live `compose up` run and judge walkthrough.
- No blockers introduced. v1 scope lock (D-07) respected: English text chat only, no new features.

---

*Phase: 07-demo-hardening*
*Completed: 2026-09-11*

## Self-Check: PASSED

- Dockerfile: FOUND `FROM python:3.12-slim-bookworm` + `uvicorn main:app`; zero `^ENV (OPENROUTER|WEATHER)` lines
- frontend/Dockerfile: FOUND `ARG NEXT_PUBLIC_WEATHERGPT_API` + `node:20-alpine` (x3 stages) + `node server.js`
- frontend/next.config.mjs: FOUND `output: "standalone"`
- compose.yaml: FOUND backend + frontend + `env_file: .env` + `NEXT_PUBLIC_WEATHERGPT_API` + ports 8000/3000; `docker compose config --quiet` exit 0
- README.md: FOUND all 8 content gates (compose up, both ports, 10 min, trio exact, OPENROUTER_API_KEY)
- scripts/demo_smoke.py: FOUND trio strings + `--live`; zero key prints/env reads; `--offline` exit 0
- All 6 new/modified files: zero `sk-or`/`your-key-here` markers
- Gates: `pytest tests/` 81 passed / 1 skipped; `tsc --noEmit` exit 0
- `.env` absent from `git status`, `git check-ignore -q .env` exit 0, never staged
- Commits: none possible (index.lock) — recorded as UNCOMMITTED/blocked, not narrated as done
