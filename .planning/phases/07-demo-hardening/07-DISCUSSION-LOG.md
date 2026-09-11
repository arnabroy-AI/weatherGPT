# Phase 7: Demo hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 7-Demo hardening
**Areas discussed:** Env repair, Docker shape, Demo script, Scope lock

---

## Env repair

| Option | Description | Selected |
|--------|-------------|----------|
| Human fixes | Grant Modify, delete index.lock, gitignore .env, then verify | ✓ |
| Phase attempts | Try repairs, degrade gracefully | |

**User's choice:** Human fixes

---

## Docker shape

| Option | Description | Selected |
|--------|-------------|----------|
| Compose pair | Backend uvicorn + frontend standalone | ✓ |
| Backend only | Frontend via npm locally | |

**User's choice:** Compose pair

| Option | Description | Selected |
|--------|-------------|----------|
| Host env file | Gitignored .env at runtime | ✓ |
| Example baked | Keys baked + docs | |

**User's choice:** Host env file

---

## Demo script

| Option | Description | Selected |
|--------|-------------|----------|
| 10-min flow | Clone → env → compose → 3 chats ≤10 min | ✓ |
| Local only | uvicorn + npm, compose best-effort | |

**User's choice:** 10-min flow

| Option | Description | Selected |
|--------|-------------|----------|
| Current trio | Current + weekend + Nashik agri | ✓ |
| Custom trio | User-named queries | |

**User's choice:** Current trio

| Option | Description | Selected |
|--------|-------------|----------|
| Harden now | CORS allowlist + throttle land | ✓ |
| Stay open | Demo runs open | |

**User's choice:** Harden now

---

## Scope lock

| Option | Description | Selected |
|--------|-------------|----------|
| Lock v1 | English text chat; v2 stays v2 | ✓ |
| Add one | Pull one v2 item in | |

**User's choice:** Lock v1

---

## Agent's Discretion

- Compose layout, README structure, throttle limits, CORS var naming.

## Deferred Ideas

- v2 items confirmed out; IMD cutover separate track.
