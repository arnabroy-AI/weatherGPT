---
phase: 06-chat-ui-wiring
plan: "02"
subsystem: chat-expansion
tags: [chat, badges, starters, states, history-cap, contract-test, nextjs]
requires: [06-01-chat-tracer]
provides: [chat-badges-bubbles, chat-starters, chat-location-states, history-cap-50]
affects: [06-03-mobile-a11y-panels]
tech-stack:
  added: []
  patterns: [abort-previous-send, status-preserving-api-error, in-memory-capped-history]
key-files:
  created:
    - frontend/components/chat/alert-badge.tsx
    - frontend/components/chat/message-bubble.tsx
    - frontend/components/chat/starters.tsx
    - frontend/components/chat/location-bar.tsx
    - frontend/components/chat/chat-states.tsx
  modified:
    - frontend/app/chat/page.tsx
    - frontend/lib/chat-client.ts
    - frontend/lib/__tests__/chat-contract.test.mjs
decisions: []
metrics:
  duration: "2026-09-11"
  completed: 2026-09-11
status: complete
---

# Phase 6 Plan 02: Badges, Bubbles, Starters, Location, States, History Cap Summary

Full conversational UX on the Plan 01 tracer slice: data-color alert badges byte-matching alerts-showcase, distinct user/assistant bubbles with Orange/Red edge, three byte-match starter chips, session location bar feeding every send, empty/loading/error/trim states per copy contract, and a 50-exchange in-memory history cap — all locked by an extended dependency-free contract test. tsc clean, 18/18 contract assertions green, temp-dir production build green with `/chat` prerendered.

## Tasks Completed

| # | Name | Files | Verification |
|---|------|-------|--------------|
| 1 | Alert badges plus message bubbles plus starters | `frontend/components/chat/alert-badge.tsx`, `frontend/components/chat/message-bubble.tsx`, `frontend/components/chat/starters.tsx` | `npx tsc --noEmit` exit 0 in `frontend/` |
| 2 | Location bar plus history cap plus chat states wired into page | `frontend/components/chat/location-bar.tsx`, `frontend/components/chat/chat-states.tsx`, `frontend/app/chat/page.tsx`, `frontend/lib/chat-client.ts`, `frontend/lib/__tests__/chat-contract.test.mjs` | `node --test` 18/18 pass; temp-dir `npm run build` exit 0, `/chat` 6.37 kB prerendered |

## Key Decisions

None — plan executed exactly as written; D-03 (location feeds every request), D-04 (badges + in-memory history), D-05 (seeded starters + designed states) followed verbatim.

## Deviations from Plan

None - plan executed exactly as written.

### Implementation notes (not deviations)

- `ChatApiError extends Error { status }` added to `chat-client.ts` so the page can map 422 to inline validation copy while quoting 502/500 `detail` verbatim as text nodes (T-06-03: never HTML). Non-2xx message strings are unchanged, so prior contract assertions still hold.
- Abort-previous-send uses a per-send sequence guard: a stale (aborted) send returns early in `catch`/`finally`, so it can neither clobber the failure card nor clear the new send's `inFlight` flag.
- On error the typed message is preserved as the visible user bubble plus the retry payload (`failure.message`/`failure.location` re-sent identically); the location bar value is never cleared. No draft-restore duplication.
- History trim runs only on assistant-append (complete exchanges), slicing to the newest 100 bubbles and flipping a single `trimmed` flag for the one center `TrimNotice`.
- Two Plan 01 contract assertions were relocated (not weakened) to their new owners: the location-placeholder check now reads `location-bar.tsx`, and the `whitespace-pre-wrap` / no-`dangerouslySetInnerHTML` check now covers all six chat sources.

## Verification Evidence

- **tsc:** `npx tsc --noEmit` in `H:/weatherGPT/frontend` → exit 0, zero errors.
- **Contract test:** `node --test frontend/lib/__tests__/chat-contract.test.mjs` → 18 pass / 0 fail (10 carried-over wire/shell assertions with 2 relocated to component owners + 7 new Plan 02 assertions + 1 mocked round-trip). New assertions extract the four `badgeClass` strings from `alerts-showcase.tsx` and the three `query` strings from `live-demo-teaser.tsx` at test time and require byte-presence in `alert-badge.tsx` / `starters.tsx`, plus copy-contract, 50-cap, no-`localStorage`, and abort/disabled-Send checks.
- **Build (temp dir, H:/ no-delete ACL):** robocopy `frontend/` (minus `node_modules`/`.next`) → `%TEMP%\weathergpt-build-0602`, then robocopy `node_modules`, `npm run build` → exit 0, `✓ Compiled successfully`, `✓ Generating static pages (5/5)`, `/chat` 6.37 kB prerendered as static content.
- **Backend untouched:** no Python files modified; no new npm packages installed (T-06-SC upheld — shadcn + lucide-react only).

## Threat Flags

None — no new surface beyond the plan's threat model. T-06-03 mitigated (error `detail` rendered via `{detail}` text node in `ErrorCard`, asserted no-`dangerouslySetInnerHTML` across all chat sources). T-06-04 upheld (location passed through as an opaque string, no client-side parsing). T-06-SC upheld (zero installs).

## Known Stubs

None — mobile dock polish, unreachable panel, and a11y extras remain scoped to Plan 03, not stubs.

## Git

Best-effort per plan environment notes (stale-lock risk; never blocking). **Result: commits NOT created** — `git add` fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (same pre-existing stale lock reported in 06-01-SUMMARY; lock file deliberately left untouched). All working-tree files are in place and verified; commit on next run after lock clears: `frontend/components/chat/*.tsx` (5 new), `frontend/app/chat/page.tsx`, `frontend/lib/chat-client.ts`, `frontend/lib/__tests__/chat-contract.test.mjs`, plus this SUMMARY. `.env` files never staged or committed.

## Self-Check: PASSED

- `frontend/components/chat/alert-badge.tsx` FOUND (exports `ALERT_BADGE_CLASSES`, `AlertBadge`, null on unknown).
- `frontend/components/chat/message-bubble.tsx` FOUND (exports `UserBubble`, `AssistantBubble`, Orange/Red edge, zero `dangerouslySetInnerHTML`).
- `frontend/components/chat/starters.tsx` FOUND (exports `STARTER_QUERIES` with the 3 exact strings + source note).
- `frontend/components/chat/location-bar.tsx` FOUND (label, placeholder, hint, MapPin).
- `frontend/components/chat/chat-states.tsx` FOUND (exports `EmptyState`, `LoadingBubble`, `ErrorCard`, `TrimNotice`).
- `frontend/app/chat/page.tsx` FOUND (LocationBar, EmptyState, MAX_EXCHANGES=50, abort-previous, 422 copy).
- `frontend/lib/__tests__/chat-contract.test.mjs` FOUND (18/18 green).
- SUMMARY file itself written at `.planning/phases/06-chat-ui-wiring/06-02-SUMMARY.md`.
