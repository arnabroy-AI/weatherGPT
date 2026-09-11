---
phase: 06-chat-ui-wiring
plan: "01"
subsystem: chat-tracer
tags: [chat, tracer, fetch-client, contract-test, nextjs]
requires: [05-frontend-shell-landing]
provides: [chat-client-direct-fetch, chat-route-shell, chat-contract-test]
affects: [06-02-badges-history, 06-03-states-panels]
tech-stack:
  added: []
  patterns: [direct-client-fetch-no-proxy, abort-controller-timeout, text-node-reply-rendering]
key-files:
  created:
    - frontend/lib/chat-client.ts
    - frontend/app/chat/page.tsx
    - frontend/lib/__tests__/chat-contract.test.mjs
  modified: []
decisions: []
metrics:
  duration: "2026-09-11T13:30Z to 2026-09-11T14:35Z (~65 min wall, incl. temp-dir build setup)"
  completed: 2026-09-11
status: complete
---

# Phase 6 Plan 01: /chat Tracer Shell + Composer + Mocked Round-Trip Summary

Production-quality `/chat` route shell with location bar, message log, and composer wired through a direct-fetch client (`POST {NEXT_PUBLIC_WEATHERGPT_API}/api/chat`, 10s `AbortController` timeout, single-JSON response), locked to the frozen backend by a dependency-free contract test. Typecheck clean, all 11 contract assertions green, temp-dir production build green with `/chat` prerendered.

## Tasks Completed

| # | Name | Files | Verification |
|---|------|-------|--------------|
| 1 | End-to-end /chat shell plus composer plus one mocked round-trip | `frontend/lib/chat-client.ts`, `frontend/app/chat/page.tsx` | `npx tsc --noEmit` exit 0 in `frontend/` |
| 2 | Contract test locking frontend shapes to backend plus build gate | `frontend/lib/__tests__/chat-contract.test.mjs` | `node --test` 11/11 pass; temp-dir `npm run build` exit 0, `/chat` 5.03 kB prerendered |

## Key Decisions

None — plan executed exactly as written; D-01 (direct fetch), D-02 (single JSON), D-03 (location bar feeds every request) followed verbatim.

## Deviations from Plan

None - plan executed exactly as written.

### Implementation notes (not deviations)

- `sendChatMessage` accepts an optional `init` (`{ signal, baseUrl }`) for testability/future Abort-on-new-send; the page currently relies on the `inFlight` guard to prevent double-submit per spec (abort-previous-send lands with Plan 02/03 expansion if needed).
- Contract test's mocked round-trip drives `fetch` directly (plain-node cannot import `.ts`); the client-side wire shape is additionally asserted statically against `chat-client.ts` source (`fetch(\`${base}/api/chat\`` regex assertion).
- `schemas/chat.py` types `location` as `Optional[str]` (default `None`) while the frontend always sends a string (empty when blank) — matches the plan directive ("never null or undefined") and is accepted by the backend schema.

## Verification Evidence

- **tsc:** `npx tsc --noEmit` in `H:/weatherGPT/frontend` → exit 0, zero errors.
- **Contract test:** `node --test frontend/lib/__tests__/chat-contract.test.mjs` → 11 pass / 0 fail (10 shape/shell assertions + 1 mocked round-trip).
- **Build (temp dir, H:/ no-delete ACL):** robocopy `frontend/` (minus `node_modules`/`.next`) → `%TEMP%\weathergpt-build-0601`, then robocopy `node_modules` (symlink `mklink /D` denied — insufficient privilege), `npm run build` → exit 0, `✓ Compiled successfully`, `✓ Generating static pages (5/5)`, `/chat` 5.03 kB prerendered as static content. Temp build log path: `C:\Users\USER\AppData\Local\Temp\weathergpt-build-0601`.
- **Backend untouched:** `schemas/chat.py`, `api/routes.py` read-only reference only; no Python files modified.

## Threat Flags

None — no new surface beyond the plan's threat model. T-06-01 mitigated (exact `{message, location}` JSON body, `Content-Type: application/json`, replies as text nodes, no `dangerouslySetInnerHTML` — asserted in contract test). T-06-02 mitigated (backend `detail` quoted verbatim as text in error Card). T-06-SC upheld (zero new npm packages, zero installs).

## Known Stubs

None — full unreachable panel, badges, history cap, starters, and mobile dock are intentionally deferred to Plans 02–03 per the tracer scope, not stubs.

## Git

Best-effort per plan environment notes (stale-lock risk; never blocking). **Result: commits NOT created** — `git add`/`git commit` both failed with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (stale lock held by another process; lock file left untouched deliberately). Working-tree files are all in place and verified; commit on next run after lock clears: `frontend/lib/chat-client.ts`, `frontend/app/chat/page.tsx`, `frontend/lib/__tests__/chat-contract.test.mjs`, plus this SUMMARY. `.env` files never staged or committed.

## Self-Check: PASSED

- `frontend/lib/chat-client.ts` FOUND (exports `getApiBaseUrl`, `CHAT_TIMEOUT_MS = 10000`, `sendChatMessage`, no `EventSource`).
- `frontend/app/chat/page.tsx` FOUND (H1 Chat, location input placeholder, `role="log"` list, composer + Send).
- `frontend/lib/__tests__/chat-contract.test.mjs` FOUND (11/11 green).
- SUMMARY file itself written at `.planning/phases/06-chat-ui-wiring/06-01-SUMMARY.md`.
