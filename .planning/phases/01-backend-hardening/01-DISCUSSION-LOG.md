# Phase 1: Backend hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-10
**Phase:** 1-Backend hardening
**Areas discussed:** Test strategy, Error contract, Observability, Hardening limits, Rate limiting, Input limits, Pytest setup, Secret safety

---

## Test strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Mock process_chat | Patch services.agent.process_chat — fastest, route + schemas only | ✓ |
| Mock executor | Patch AgentExecutor.invoke — tests agent wiring too | |

**User's choice:** Mock process_chat
**Notes:** —

## Test strategy (gate)

| Option | Description | Selected |
|--------|-------------|----------|
| Pass + report | Pytest must pass; coverage reported but not gating | ✓ |
| 80% gate | Fail under 80% from day one | |

**User's choice:** Pass + report
**Notes:** —

## Test strategy (layout + live)

| Option | Description | Selected |
|--------|-------------|----------|
| Flat tests/ | tests/test_chat_api.py + tests/test_weather_tool.py | ✓ |
| Split suite | tests/unit + tests/integration split | |

**User's choice:** Flat tests/ + Opt-in live (skipped-by-default OpenRouter check)
**Notes:** Deterministic CI; live test only for manual runs.

---

## Error contract

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current | Missing key / LLM failure → 502; unexpected → 500 | ✓ |
| Add 504 timeout | Explicit 504 for LLM timeouts | |

**User's choice:** Keep current
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Degraded 200 | Friendly degraded reply with 200 on outage | |
| Fail loudly | Honest 502/500 so failures are visible | ✓ |

**User's choice:** Fail loudly
**Notes:** Visibility over demo smoothness in Phase 1.

| Option | Description | Selected |
|--------|-------------|----------|
| Log full, send safe | Full traceback server-side; safe detail to client | ✓ |
| Debug-gated | Traceback in response behind debug flag | |

**User's choice:** Log full, send safe
**Notes:** —

---

## Observability

| Option | Description | Selected |
|--------|-------------|----------|
| Stdlib simple | Human-readable lines, INFO default | ✓ |
| JSON logs | Structured JSON with request_id/latency | |

**User's choice:** Stdlib simple
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Add request-id | X-Request-ID echoed/generated, in logs + errors | ✓ |
| Defer tracing | Skip until Phase 7 | |

**User's choice:** Add request-id
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Keep liveness | {status, app, version} only | ✓ |
| Deep health | + OpenRouter reachability / tool status | |

**User's choice:** Keep liveness
**Notes:** —

---

## Hardening limits

| Option | Description | Selected |
|--------|-------------|----------|
| 30s + 1 retry | LLM timeout 30s, one retry, then 502 | ✓ |
| No timeout | Rely on client | |

**User's choice:** 30s + 1 retry
**Notes:** Applied in agent layer.

| Option | Description | Selected |
|--------|-------------|----------|
| Keep open | allow_origins=* for local dev; tighten in Phase 7 | ✓ |
| Lock CORS now | Restrict via env var immediately | |

**User's choice:** Keep open
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Threadpool fix | Offload sync process_chat via anyio.to_thread | ✓ |
| Defer fix | Leave until Phase 2 async work | |

**User's choice:** Threadpool fix
**Notes:** Prevents event-loop blocking.

---

## Follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| Defer throttle | No rate limiting in Phase 1; slowapi in Phase 7 | ✓ |
| Add slowapi now | In-memory per-IP limit on /chat | |

**User's choice:** Defer throttle

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as-is | message 1–2000, location ≤120, strip whitespace | ✓ |
| Tighten now | 500 chars + injection strip | |

**User's choice:** Keep as-is

| Option | Description | Selected |
|--------|-------------|----------|
| Asyncio auto | pytest + httpx ASGITransport + asyncio_mode=auto | ✓ |
| TestClient | Sync TestClient only | |

**User's choice:** Asyncio auto

| Option | Description | Selected |
|--------|-------------|----------|
| Redact + test | Never log keys; test asserts absence | ✓ |
| Trust settings | No explicit test | |

**User's choice:** Redact + test

---

## the agent's Discretion

None — all areas explicitly decided by user.

## Deferred Ideas

- Rate limiting (slowapi) → Phase 7
- CORS tightening behind env var → Phase 7
- Real IMD integration → Phase 2 (never discussed as in-scope)
