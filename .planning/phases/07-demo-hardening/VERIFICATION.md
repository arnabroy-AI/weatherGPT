---
phase: 07-demo-hardening
verified: 2026-09-11T20:00:00Z
status: passed
score: 7/7 must-haves verified
mode: offline (Docker daemon DOWN — live `compose up` out of scope per brief)
---

# Phase 7: Demo Hardening — Verification Report

**Phase Goal (ROADMAP.md):** One-command SIH demo (Docker + docs)
**Requirements:** DEMO-01, DEMO-02
**Success Criteria (ROADMAP, 2):**
1. A fresh clone follows README and reaches working chat in ≤10 min
2. `docker compose up` brings up backend + frontend with 3 seeded demo queries passing
**Verification mode:** Goal-backward, file/content based. Docker daemon is DOWN,
so live `compose up` run is out of scope; validated files + offline gates instead.
All commands below were re-run by the verifier — SUMMARY.md claims were not trusted.

## Verdict: PASSED (offline)

Both success criteria verified as far as offline possible. Live `compose up`
+ live seeded queries and git-repair are recorded as human follow-ups, not gaps.

## Observable Truths

| # | Truth | Status | Evidence (verifier re-ran) |
|---|-------|--------|----------------------------|
| 1 | README documents fresh-clone → working-chat flow (compose primary + local-dev secondary) plausibly completable in ≤10 min | ✓ VERIFIED | `README.md` read: Prerequisites (Docker, "10 min on the clock"), Quick start compose primary (`git clone`, `cp .env.example .env`, fill `OPENROUTER_API_KEY`, `docker compose up --build`, open http://localhost:3000, API at http://localhost:8000), Local-dev secondary (`uvicorn main:app` + `NEXT_PUBLIC_WEATHERGPT_API=... npm run dev`), Troubleshooting (daemon down, port busy, index.lock → ENV-REPAIR-STATUS.md), Scope note (English text chat only). Gate grep: all of `docker compose up`, `localhost:3000`, `localhost:8000`, `10 min`, `OPENROUTER_API_KEY`, `offline`, `uvicorn main:app`, `npm run dev` FOUND |
| 2 | Seeded trio present and byte-matching chat starters | ✓ VERIFIED | `python scripts/demo_smoke.py --offline` → `parity: PASS (3 queries x starters/README/teaser)`. Trio `Current weather in Pune` / `Mumbai this weekend` / `Paddy sowing advice for Nashik` FOUND in all four of `README.md`, `scripts/demo_smoke.py` SEEDED_QUERIES, `frontend/components/chat/starters.tsx` STARTER_QUERIES, `frontend/components/live-demo-teaser.tsx` SEEDED |
| 3 | `docker compose config --quiet` passes (no daemon needed) | ✓ VERIFIED | Re-ran `docker compose config --quiet` from repo root → `LASTEXITCODE=0`. Client-side validation only; daemon still down (ENV-REPAIR-STATUS.md probe stands) |
| 4 | Dockerfiles + compose + smoke exist with runtime-only keys (no baked secrets) | ✓ VERIFIED | `Dockerfile` (FROM python:3.12-slim-bookworm, uvicorn CMD, zero `^ENV` lines), `frontend/Dockerfile` (3× node:20-alpine, `ARG NEXT_PUBLIC_WEATHERGPT_API` → ENV bake of public URL only, `node server.js`), `compose.yaml` (2 services, backend `env_file: .env`, frontend build-arg `NEXT_PUBLIC_WEATHERGPT_API`, ports 8000/3000, `depends_on: backend`), `frontend/next.config.mjs` (`output: "standalone"`). Greps over Dockerfile/frontend/Dockerfile/compose.yaml for `^ENV (OPENROUTER\|WEATHER)`, `sk-or`, inline secret values → no hits. Key link: compose build-arg name matches `frontend/lib/chat-client.ts` `process.env.NEXT_PUBLIC_WEATHERGPT_API` |
| 5 | Seeded smoke passes offline | ✓ VERIFIED | Re-ran `python scripts/demo_smoke.py --offline` → `parity: PASS`, `compose: PASS (services: backend, frontend)`, `health: not running (optional probe skipped: URLError)`, `smoke: PASS (offline)`, `EXIT=True`. Script is stdlib-only, never reads `.env`/key env vars, never prints key values (only docstring mentions; no `getenv.*OPENROUTER`, no `print.*key`) |
| 6 | CORS allowlist + throttle landed with tests green | ✓ VERIFIED | Wiring: `core/config.py` (`CORS_ALLOW_ORIGINS`, `CHAT_THROTTLE_PER_MIN`, `get_cors_allow_origins()`), `main.py` (CORSMiddleware reads helper, `allow_credentials` only for explicit list), `api/routes.py` (POST /api/chat → `check_rate_limit(client_ip)` → 429 + `Retry-After` via `sanitize_detail`), `api/throttle.py` (monotonic+Lock sliding window, `reset_rate_limiter`), `tests/conftest.py` (autouse `reset_rate_limiter`). Gates re-run: `python -m pytest tests/test_demo_hardening.py -v` → 5 passed; `python -m pytest tests/ -q` → 81 passed, 1 skipped; `npx tsc --noEmit` from `frontend/` cwd → exit 0; `node --test frontend/lib/__tests__/chat-contract.test.mjs` → 21 pass, 0 fail |
| 7 | .env ignored; no v1 scope creep | ✓ VERIFIED | `.gitignore:2` is exactly `.env`; `git check-ignore -v .env` → `.gitignore:2:.env`; `git status --short` lists `.env.example` but NOT `.env`. `.dockerignore` excludes `.env`, `.env.local`, `node_modules`, `__pycache__`, `.planning`, `.git`. Scope: grep for `multilingual\|Hindi\|voice input\|radar\|satellite map\|OAuth\|subscription` over new files hits only `README.md:90` scope-lock note ("deferred to v2") — no implementation creep. Anti-pattern scan (`TODO\|FIXME\|XXX\|TBD\|placeholder\|coming soon`) over new files → no hits |

**Score:** 7/7 truths verified, 0 failed.

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| DEMO-01 | Full stack runs locally (uvicorn + frontend dev server) documented in README | ✓ SATISFIED | README Quick start (compose primary) + Local dev (secondary) sections verified above |
| DEMO-02 | Repo ships Dockerfile/docker-compose for one-command SIH demo + seeded demo queries | ✓ SATISFIED (offline) | Dockerfiles + compose.yaml validate (`config --quiet` exit 0), keys runtime-only, seeded trio smoke PASS offline; live `up` is human follow-up |

## Key Links

| From | To | Via | Status |
|------|----|-----|--------|
| compose.yaml frontend build arg | frontend chat-client | `NEXT_PUBLIC_WEATHERGPT_API` in both | ✓ WIRED |
| README seeded strings | starters.tsx STARTER_QUERIES | byte-match, smoke asserts | ✓ WIRED |
| scripts/demo_smoke.py | compose validity + starter parity | parses services, checks env_file/build-arg | ✓ WIRED |
| main.py CORS middleware | core/config.py allowlist helper | `get_cors_allow_origins()` | ✓ WIRED |
| POST /api/chat | api/throttle.py | `check_rate_limit` before agent, 429 + Retry-After | ✓ WIRED |
| tests/conftest.py | throttle store | `reset_rate_limiter` autouse | ✓ WIRED |

## Gates Re-run (verifier, not SUMMARY)

| Gate | Command | Result |
|------|---------|--------|
| compose config | `docker compose config --quiet` | exit 0 |
| smoke offline | `python scripts/demo_smoke.py --offline` | `smoke: PASS (offline)` |
| backend suite | `python -m pytest tests/ -q` | 81 passed, 1 skipped |
| hardening slice | `python -m pytest tests/test_demo_hardening.py -v` | 5 passed |
| frontend types | `npx tsc --noEmit` (from `frontend/` cwd) | exit 0 |
| chat contract | `node --test frontend/lib/__tests__/chat-contract.test.mjs` | 21 pass, 0 fail |
| ignore hygiene | `git check-ignore -v .env` + `git status --short` | ignored, not listed |
| secret hygiene | grep Dockerfiles/compose for baked secrets | no hits |

Note: `npx --prefix frontend tsc --noEmit` from repo root prints tsc help
(exit 1) — pre-existing cwd quirk already documented in both plan SUMMARIES.
The identical check from `frontend/` cwd exits 0. Not a gap.

## Human Follow-ups (NOT gaps)

1. **Live compose run** — Docker daemon is DOWN. Human: start Docker Desktop,
   run `docker compose up --build`, open http://localhost:3000, send the three
   seeded queries, optionally `python scripts/demo_smoke.py --live`.
2. **Git repair** — stale `.git/index.lock` + zero-commit repo + `RX,W`-only ACL
   persist (see `ENV-REPAIR-STATUS.md`). Human: verify no git process runs,
   delete `.git/index.lock`, grant Modify, initial commit excluding `.env`.

## Gaps

None. No BLOCKERs, no WARNINGs in offline scope.

---
_Verified: 2026-09-11T20:00:00Z_
_Verifier: the agent (gsd-verifier, offline mode)_
