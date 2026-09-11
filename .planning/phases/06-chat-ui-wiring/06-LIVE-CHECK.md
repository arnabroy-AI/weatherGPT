# Phase 6: Live completion check

**Date:** 2026-09-11
**Method:** Live HTTP against user's running servers (backend :8000, frontend :3000)

## Backend (`POST /api/chat` × trio)
- Current Pune / Mumbai weekend / Nashik agri → all `502` with safe detail
  (`OpenRouter 401 User not found` — placeholder key in `.env`).
- Verdict: fail-loudly contract working, zero leaks. Live answers need a real
  `OPENROUTER_API_KEY`.

## Frontend (`/` + `/chat`, both HTTP 200)
- Landing 200 (~95KB). Chat 200 (~19KB), location bar + Send present.
- Chat renders the **missing-env UnreachablePanel variant** ("not configured"):
  the dev server was started without `NEXT_PUBLIC_WEATHERGPT_API` in its
  environment, so per D-08 it correctly shows the panel instead of starters.
  This is the specified behavior, not a bug.
- Starters trio, badge classes, unreachable fetch-failure panel: all present in
  source (`starters.tsx`, `chat-states.tsx`, `unreachable-panel.tsx`), wired in
  `app/chat/page.tsx`, covered by 21 contract tests. Not visible in served HTML
  only because the env-missing branch takes precedence.

## Required user actions to finish live proof
1. `frontend/.env.local` ← `NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000`
   (or export it in the same terminal BEFORE `npm run dev`), restart dev.
2. Real `OPENROUTER_API_KEY` in root `.env`, restart backend.
3. Send the trio in the browser; expect Green/Yellow/Orange badges + advisories.

## Verdict
Phase 6 code-complete and verified (static + contract + file/content gates).
Live browser proof pending the two user-side env fixes above.
