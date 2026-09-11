---
phase: 06-chat-ui-wiring
plan: "03"
subsystem: chat-hardening
tags: [chat, unreachable-panel, composer, a11y, mobile-dock, slop-gates, pytest-guard, nextjs]
requires: [06-02-badges-history]
provides: [chat-unreachable-env-states, chat-accessible-composer, chat-a11y-contract, chat-mobile-dock]
affects: []
tech-stack:
  added: []
  patterns: [zero-message-unreachable-routing, manual-retry-identical-payload, focus-restore-without-theft]
key-files:
  created:
    - frontend/components/chat/unreachable-panel.tsx
    - frontend/components/chat/composer.tsx
  modified:
    - frontend/app/chat/page.tsx
    - frontend/lib/__tests__/chat-contract.test.mjs
decisions:
  - Unreachable routing keys on pre-send history: zero prior messages plus a non-HTTP error renders the full panel; any history (or any ChatApiError) renders the inline ErrorCard.
  - Shared Header left untouched (outside plan files): its landing CTA remains; chat adds its own Back-to-home plus Clear row.
metrics:
  duration: "2026-09-11"
  completed: 2026-09-11
status: complete
---

# Phase 6 Plan 03: Unreachable Panel, Env Handling, Composer, A11y, Mobile, Slop Gates Summary

Demo-proof hardening on the Plan 02 slice: a friendly dead-backend/bad-env panel that always names the exact configured URL with manual Retry, `NEXT_PUBLIC_WEATHERGPT_API` handling with a no-fetch not-configured state, an extracted docked `Composer` (Enter/Shift+Enter/Escape, 44px targets, in-flight disable), the full D-07 accessibility contract (skip link, live regions, focus flows, reduced-motion backstop), the 390px docked layout with no overlap, clean slop gates, and a green frozen-backend pytest guard. tsc clean, contract test 21/21, temp-dir production build green with `/chat` prerendered at 7.71 kB, backend pytest 76 passed / 1 skipped.

## Tasks Completed

| # | Name | Files | Verification |
|---|------|-------|--------------|
| 1 | Unreachable panel plus env handling plus composer extraction | `frontend/components/chat/unreachable-panel.tsx`, `frontend/components/chat/composer.tsx`, `frontend/app/chat/page.tsx` | `npx tsc --noEmit` exit 0 in `frontend/` |
| 2 | A11y pass plus mobile plus slop gates plus backend regression guard | `frontend/app/chat/page.tsx`, `frontend/components/chat/composer.tsx` (`.env.local.example` verified untouched, line preserved) | `python -m pytest tests/ -q` → 76 passed, 1 skipped |

## Key Decisions

- **Unreachable routing keys on pre-send history (D-08):** `send()` snapshots `hadMessages` before appending the optimistic user bubble. Zero prior messages plus a non-HTTP error (network failure, timeout, missing env) sets `UnreachableSend` and renders the full `UnreachablePanel` below the attempted bubble; any history — or any `ChatApiError` (422/502/500) — renders the inline `ErrorCard`. The panel Retry re-sends the identical `{message, location}` once per click; Send stays disabled while in-flight (T-06-06, no auto-backoff).
- **Shared Header left untouched:** `frontend/components/header.tsx` is outside this plan's `files_modified`, so its landing CTA ("Try a sample question" → `#live-demo`) still renders on `/chat`. The chat page adds its own header row with `Back to home` (`/`) plus `Clear conversation` instead. Re-pointing or hiding the shared CTA is deferred to a plan that owns the header.
- **Focus restore without theft (D-07):** on settle, focus returns to the composer only when it was lost to `<body>` (Send disabling drops it); focus the user moved elsewhere mid-flight is never stolen, and reply arrival never moves focus — the `role="log"` polite region announces.
- **Reduced-motion without touching chat-states:** `chat-states.tsx` is outside `files_modified`, so the static-skeleton backstop is a page-level `<style>` media query (`prefers-reduced-motion: reduce` → `.chat-loading-static *{animation:none}`) wrapping `LoadingBubble`, plus instant (non-smooth) auto-scroll via `matchMedia`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan 02 contract test broke on the mandated composer extraction**
- **Found during:** Task 2 (contract-test gate run: 1 failure, then a syntax break from the fix itself)
- **Issue:** `chat-contract.test.mjs` asserted `aria-label="Type your weather question"` and `aria-label="Send message"` inside `page.tsx` source; the plan-mandated extraction moved both into `composer.tsx`. The first repair edit also dropped a `describe` closing brace (syntax error), fixed immediately.
- **Fix:** test now reads `composer.tsx` + `unreachable-panel.tsx` as named sources (same relocation precedent as Plan 02's location-bar move), redirects the two aria-label assertions to `composerSrc`, extends the no-`dangerouslySetInnerHTML` and no-`localStorage` loops to both new files, and adds a Plan 03 describe with 3 new tests (unreachable copy contract, composer keys/dock, a11y rows). `composer.tsx` was also switched from constant-referenced to literal `aria-label`/`placeholder` attributes so the contract assertions stay byte-literal.
- **Files modified:** `frontend/lib/__tests__/chat-contract.test.mjs` (outside plan `files_modified` — required to keep the phase lock green), `frontend/components/chat/composer.tsx`
- **Commit:** uncommitted (git blocked, see below)

**2. [Rule 1 - Bug] React 18 ref-type mismatch in extracted Composer**
- **Found during:** Task 1 (`npx tsc --noEmit` → TS2322 on the textarea `ref`)
- **Issue:** prop typed `RefObject<HTMLTextAreaElement | null>` is not assignable to the textarea `ref` under `@types/react` 18.
- **Fix:** prop narrowed to `RefObject<HTMLTextAreaElement>`; page passes `useRef<HTMLTextAreaElement>(null)`. tsc exit 0 after.
- **Files modified:** `frontend/components/chat/composer.tsx`, `frontend/app/chat/page.tsx`
- **Commit:** uncommitted (git blocked, see below)

## Verification Evidence

- **tsc:** `npx tsc --noEmit` in `H:/weatherGPT/frontend` → exit 0, zero errors (`TSC-CLEAN`).
- **Contract test:** `node --test frontend/lib/__tests__/chat-contract.test.mjs` → **21 pass / 0 fail** (18 carried Plan 01+02 assertions + 3 new Plan 03 assertions; badge byte-match vs `alerts-showcase` and starter byte-match vs `live-demo-teaser` still green).
- **Backend regression guard:** `python -m pytest tests/ -q` from `H:/weatherGPT` → **76 passed, 1 skipped in 9.56s**. No Python file touched; frozen backend proven untouched.
- **Build (temp dir, H:/ no-delete ACL):** robocopy `frontend/` (minus `node_modules`/`.next`, excluding `.env*`) → `C:\Users\USER\AppData\Local\Temp\weathergpt-build-0603`, robocopy `node_modules`, `npm run build` → exit 0, `✓ Compiled successfully`, `✓ Generating static pages (5/5)`, `/chat` **7.71 kB** prerendered as static content, zero type errors.
- **A11y grep gate:** `role="log"`, `aria-live="polite"`, `aria-atomic="false"`, `aria-label="Conversation"`, `role="status"` (loading, trim, cleared-announcement), `role="alert"` (ErrorCard + UnreachablePanel), `aria-label`s (composer, Send, Clear, badges), `Skip to content` → `#main-content`, `tabIndex={-1}` H1 with route-entry focus — all present in `page.tsx`/`composer.tsx`/`chat-states.tsx`.
- **390px mobile gate (static):** header row compresses (H1 `text-xl` → `md:text-2xl`, Clear icon-only `h-11 w-11` with `aria-label`); location bar already full-width stacked; bubbles user 85% right / assistant 100% left single column; composer `sticky bottom-0` + `p-3` + `pb-[calc(0.75rem+env(safe-area-inset-bottom))]` + hairline border; message list `pb-4` + `gap-3 md:gap-4`; Send/Clear/chips all ≥44px; no device-lab run in this environment — recorded as static verification.
- **Slop gates:** `lorem` (case-insensitive), purple/blue gradient strings (`from-purple|via-purple|to-blue|from-indigo|linear-gradient|bg-gradient`), and `dangerouslySetInnerHTML` across `app/chat/` + `components/chat/` → **zero matches**; `git ls-files` shows **zero tracked `.env*` files** (nothing committed yet — see Git); `frontend/.env.local.example` untouched on disk, still carrying `NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000`.
- **Threat dispositions:** T-06-05 upheld (panel echoes only the public base URL as a text-node `<code>`, never keys); T-06-06 mitigated (Send `disabled` + `aria-disabled` with spinner in-flight, abort-previous-send, manual Retry only); T-06-SC upheld (zero new packages, zero installs).

## Known Stubs

None — every Plan 03 scope item is implemented; the shared-header CTA note above is a documented deferral, not a stub.

## Git

Best-effort per plan environment notes (never blocking). **Result: commits NOT created** — `git add` fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (same pre-existing stale lock reported in 06-01/06-02; lock deliberately left untouched), and the repo additionally has **zero commits on `main`** (`git log` → "does not have any commits yet"), so there is no HEAD to attach to either. All working-tree files are in place and verified; commit everything once the lock clears and the repo is initialized: `frontend/components/chat/unreachable-panel.tsx`, `frontend/components/chat/composer.tsx`, `frontend/app/chat/page.tsx`, `frontend/lib/__tests__/chat-contract.test.mjs`, plus this SUMMARY. `.env` files must never be staged (only `.env.local.example`).

## Self-Check: PASSED

- `frontend/components/chat/unreachable-panel.tsx` FOUND (exports `UnreachablePanel`, `UNREACHABLE_HEADING`, `UNREACHABLE_MISSING_ENV_URL`, `role="alert"`, Retry).
- `frontend/components/chat/composer.tsx` FOUND (exports `Composer`, Enter/Shift+Enter/Escape, `sticky bottom-0`, safe-area, 44px Send with spinner).
- `frontend/app/chat/page.tsx` FOUND (skip link, `#main-content`, Clear confirm, `Back to home`, unreachable routing, focus flows, reduced-motion).
- `frontend/lib/__tests__/chat-contract.test.mjs` FOUND (21/21 green).
- SUMMARY file itself written at `.planning/phases/06-chat-ui-wiring/06-03-SUMMARY.md`.
