# Phase 6: Chat UI wiring - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Build the `/chat` route: glassmorphism conversational UI calling `POST {NEXT_PUBLIC_WEATHERGPT_API}/api/chat` directly. Location bar, alert badges, in-memory history, seeded starters, full states, mobile dock, a11y, friendly unreachable panel. No backend changes, no streaming, no deploy.

## Implementation Decisions

### Chat transport
- **D-01:** Direct client `fetch` to the backend (CORS already open). No Next.js proxy route.
- **D-02:** Single JSON response per message (today's API shape). No streaming.

### Chat UX states
- **D-03:** Location bar adjacent to the chat header; its value feeds every request's `location` field.
- **D-04:** Alert badges mapped Green/Yellow/Orange/Red per `alert_level`; conversation history kept in-memory (no persistence).
- **D-05:** Landing teaser's 3 seeded queries as clickable starters; designed empty / loading / error states (not bare input).

### Mobile + a11y
- **D-06:** 390px: bottom-docked input, stacked messages, no overlap.
- **D-07:** Full a11y: ARIA live regions for replies, labelled controls, sane focus management.

### Unreachable UX
- **D-08:** Dead backend / bad env → friendly panel naming what happened + Retry button + the configured backend URL shown. Never a blank screen.

### Claude's Discretion
- Message bubble styling within tokens, retry/backoff timing, history cap length.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- Backend (frozen): `POST {base}/api/chat {message, location} → {reply, alert_level}`; error shapes 422/502/500 with safe `detail`.
- `frontend/.env.local.example` — `NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000`.
- `frontend/app/page.tsx`, `frontend/components/live-demo-teaser.tsx` — seeded queries + voice to reuse.
- `frontend/components/` shell + tokens (teal/amber, Grotesk/Inter, shadcn) — chat matches the system.
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (FRNT-03, FRNT-04), `.planning/ROADMAP.md` (Phase 6 goal + criteria).
- `.planning/phases/05-frontend-shell-landing/05-UI-SPEC.md`, `05-CONTEXT.md` — design authority.

## Existing Code Insights

### Reusable Assets
- shadcn Button/Badge/Card + Sheet/DropdownMenu (import-ready) — badges for alert levels, cards for messages/errors.
- Teaser's 3 seeded queries + honesty note — starters reuse the exact strings.
- Alert four-state data colors from alerts-showcase — badge mapping must match.
- Theme toggle + light/dark tokens — chat inherits both modes.

### Established Patterns
- Stock shadcn + Tailwind CSS variables; `next/font`; 390px base; anti-slop bans (no gradients-as-crutch, no lorem, no clipart).
- `npm run build` via temp-dir copy (H:/ no-delete ACL); `npx tsc --noEmit` safe in place.

### Integration Points
- New `frontend/app/chat/page.tsx` (+ colocated components); env read at runtime with missing-env friendly state.
- 8s answer budget per roadmap criterion — loading state + fetch timeout aligned (~10s client timeout, abortable).

## Specific Ideas

No specific requirements — open to standard approaches within the design system.

## Deferred Ideas

- Streaming tokens → post-v1 (needs backend SSE). History persistence/accounts → v2. Deploy → Phase 7.

---

*Phase: 6-Chat UI wiring*
*Context gathered: 2026-09-11*
