# Phase 7: Demo hardening - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

SIH demo readiness: environment repairs verified, `docker compose up` for backend + frontend, README 10-minute flow, 3 seeded queries green, deferred CORS + throttle landed. No new features, v1 scope locked.

## Implementation Decisions

### Env repair
- **D-01:** HUMAN prerequisite before/withside this phase: grant Modify on `H:/weatherGPT` (or relocate repo), delete stale `.git/index.lock`, gitignore root `.env`, initial commit. Phase verifies repairs; it does not re-attempt blocked mutations blindly.

### Docker shape
- **D-02:** `docker compose` runs the pair: backend (uvicorn) + frontend (Next.js standalone output).
- **D-03:** Keys via host `.env` file (gitignored) mounted/provided at runtime. Never baked into images.

### Demo script
- **D-04:** README flow: fresh clone → env → `compose up` → 3 seeded chats green in ≤10 min.
- **D-05:** Seeded trio: current-weather query + weekend forecast + Nashik agri advisory.
- **D-06:** Deferred hardening lands now: CORS env allowlist (replacing `*` when set) + per-IP throttle on `/chat`.

### Scope lock
- **D-07:** v1 locked: multilingual, voice, maps, accounts stay v2. Demo is English text chat.

### Claude's Discretion
- Compose file layout, README structure, throttle limits, CORS var naming.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- Backend: `POST /api/chat`, `GET /health`, CORS middleware site (`main.py`), no-throttle baseline.
- Frontend: `NEXT_PUBLIC_WEATHERGPT_API`, standalone-output readiness, `/chat` route.
- `.env.example` (backend keys), `frontend/.env.local.example` (base URL).
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (DEMO-01, DEMO-02), `.planning/ROADMAP.md` (Phase 7 criteria).
- Prior CONTEXTs: D-12/D-14 (deferrals landing now), D-09 (disclosure voice for README).

## Existing Code Insights

### Reusable Assets
- `main.py` CORS block — allowlist reads env, defaults to `*` local-dev when unset.
- Seeded queries already exist as chat starters (byte-match) — demo script reuses them.
- Recorded fixtures + MockTransport — compose smoke test can run offline-capable checks; live LLM call needs a real key (documented, opt-in).

### Established Patterns
- Sanitize/redact, log-full/send-safe — compose logs must not leak keys.
- Temp-dir builds for frontend (until ACL fixed); pytest guard stays green.

### Integration Points
- `Dockerfile` (backend) + `frontend/Dockerfile` + root `compose.yaml`; `.dockerignore` excluding `.env`, `node_modules`, `__pycache__`, `.planning` bulk.
- README at repo root documents both flows (compose primary, local-dev secondary).

## Specific Ideas

No specific requirements — standard compose + README conventions.

## Deferred Ideas

- v2: multilingual, voice, maps, accounts. Post-v1: streaming, persistence. IMD-direct cutover: separate track.

---

*Phase: 7-Demo hardening*
*Context gathered: 2026-09-11*
