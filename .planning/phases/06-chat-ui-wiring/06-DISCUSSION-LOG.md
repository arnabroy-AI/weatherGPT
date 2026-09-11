# Phase 6: Chat UI wiring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 6-Chat UI wiring
**Areas discussed:** Chat transport, Chat UX states, Mobile + a11y, Unreachable UX

---

## Chat transport

| Option | Description | Selected |
|--------|-------------|----------|
| Direct fetch | Client fetch to backend, CORS open | ✓ |
| Proxy route | Next.js /api/chat proxy | |

**User's choice:** Direct fetch

| Option | Description | Selected |
|--------|-------------|----------|
| Single response | One JSON per message | ✓ |
| Streaming | Token streaming (needs SSE) | |

**User's choice:** Single response

---

## Chat UX states

| Option | Description | Selected |
|--------|-------------|----------|
| Location bar | Header-adjacent field feeding requests | ✓ |
| No input | Agent asks when needed | |

**User's choice:** Location bar

| Option | Description | Selected |
|--------|-------------|----------|
| Badges + memory | Alert badges + in-memory history | ✓ |
| Badges only | No history | |

**User's choice:** Badges + memory

| Option | Description | Selected |
|--------|-------------|----------|
| Seeded + states | Clickable starters + empty/loading/error | ✓ |
| Bare input | Blank input, inline errors | |

**User's choice:** Seeded + states

---

## Mobile + a11y

| Option | Description | Selected |
|--------|-------------|----------|
| Docked input | Bottom-docked, stacked, 390px clean | ✓ |
| Scaled same | Desktop layout scaled | |

**User's choice:** Docked input

| Option | Description | Selected |
|--------|-------------|----------|
| Full a11y | Live regions, labels, focus | ✓ |
| Semantic only | Plain semantics | |

**User's choice:** Full a11y

---

## Unreachable UX

| Option | Description | Selected |
|--------|-------------|----------|
| Friendly + retry | Panel + Retry + URL shown | ✓ |
| Inline only | Error bubble | |

**User's choice:** Friendly + retry

---

## Agent's Discretion

- Bubble styling, retry/backoff timing, history cap.

## Deferred Ideas

- Streaming → post-v1; persistence/accounts → v2; deploy → Phase 7.
