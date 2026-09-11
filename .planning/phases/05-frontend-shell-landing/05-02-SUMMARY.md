---
phase: 05-frontend-shell-landing
plan: "02"
subsystem: ui
tags: [nextjs-14, shadcn, tailwindcss, typescript, lucide-react, landing-sections]
requires: [05-01 (token system, scaffold conventions, Card/Badge usage)]
provides:
  - Four middle landing sections with exact UI-SPEC copy (features, live-demo teaser, alerts showcase, how-it-works)
  - Stock shadcn Card + Separator primitives for plan-03 page assembly
affects: [05-frontend-shell-landing plan 03 (page assembly), phase-06-chat-ui (Alert badge wording contract)]
tech-stack:
  added: []
  patterns: [glass-card sections in max-w-6xl containers, Badge level-name text never color alone, disabled-button CTA with Phase-6 caption]
key-files:
  created:
    - frontend/components/features.tsx
    - frontend/components/live-demo-teaser.tsx
    - frontend/components/alerts-showcase.tsx
    - frontend/components/how-it-works.tsx
    - frontend/components/ui/card.tsx
    - frontend/components/ui/separator.tsx
  modified: []
key-decisions:
  - "Separator implemented as a presentational stock-API component (no @radix-ui/react-separator install) to honor threat T-05-02-SC zero-new-packages"
  - "Sections NOT wired into app/page.tsx — plan-03 owns page assembly; this plan ships components only"
  - "Build proven in C:/Users/USER/AppData/Local/Temp/wgpt-build-0502/frontend (same H:/ no-delete workaround as plan-01)"
requirements-completed: [FRNT-01, FRNT-02]
status: complete
---

# Phase 05 Plan 02: Middle Landing Sections Summary

**Four middle landing sections (features, live-demo teaser, alerts showcase, how-it-works) with exact UI-SPEC copy in glass Cards — scoped anti-slop gate clean, production build green with zero type errors.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3/3 complete
- **Files created:** 6; 0 modified

## Accomplishments

- **Features (`#features`):** 6 equal glass Cards in 1col/2col-sm/3col-lg grid with distinct lucide icons and the exact six UI-SPEC bodies — Ask like you talk, Alerts you can read at a glance, 5-day outlooks, Farm advice grounded (paddy/wheat/cotton/sugarcane/maize/soybean), It asks when unsure, Honest when data fails.
- **How-it-works (`#how-it-works`):** 3 numbered glass Cards (01 You ask / 02 Tools ground it / 03 You get answer + alert with Alert: Green-to-Red line) in 1col/3col-md with a desktop connecting Separator.
- **Live-demo teaser (`#live-demo`):** glass-hero-panel (blur-lg) with heading "See what an answer looks like" + 3 seeded-query Cards (Pune 33.2°C Alert: Green / Mumbai weekend Alert: Orange (Sat) + advisory / Nashik paddy seedlings), honesty note "Sample values shown…", and "Open the chat" rendered as a **disabled button** with "Arrives in Phase 6" caption — zero `href="/chat"` anchors anywhere in frontend/.
- **Alerts showcase (`#alerts`):** 4 Cards in 1col/2col-sm/4col-lg, each headed by a Badge showing its level-name text (Green/Yellow/Orange/Red, never color alone) + `Alert:` line + advisory, plus the verbatim disclaimer: live advisories are derived estimates, never described as IMD-issued warnings (T-05-02-01).
- **Stock primitives:** `ui/card.tsx` (byte-stock shadcn), `ui/separator.tsx` (stock API, presentational — see deviation 1).
- **Scoped anti-slop gate (Task 3):** lorem=0, `<img`=0, purple/blue-gradient markers=0 (sections + ui + globals.css), `href="/chat"`=0, each section file carries 5–13 domain-string hits (IMD/Alert/monsoon/forecast/crop/district).

## Task Commits

Per-task commits were **not possible**: `git add` fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (stale lock, same as plan-01; exit 128). Per the execution brief, git was best-effort and non-blocking.

1. **Task 1: Features + how-it-works** — uncommitted (files on disk)
2. **Task 2: Teaser + alerts showcase** — uncommitted (files on disk)
3. **Task 3: Anti-slop gate** — verification only, no file changes needed (gate clean first pass)

## Files Created/Modified

- `frontend/components/features.tsx` — 6-card glass grid, id features
- `frontend/components/how-it-works.tsx` — 3-step cards + Separator, id how-it-works
- `frontend/components/live-demo-teaser.tsx` — seeded-query panel, id live-demo, disabled Phase 6 CTA
- `frontend/components/alerts-showcase.tsx` — 4-level badges, id alerts, disclaimer
- `frontend/components/ui/card.tsx`, `frontend/components/ui/separator.tsx` — stock shadcn additions
- Backend untouched; no `/chat` route created; no `.env` touched

## Decisions Made

- Separator without the Radix peer (threat T-05-02-SC forbids new packages; same `orientation`/`decorative` API, documented in-file).
- No page.tsx wiring — plan-03 assembles; this plan's files are import-ready (`Features`, `LiveDemoTeaser`, `AlertsShowcase`, `HowItWorks` named exports).
- Temp-dir build proof reused from plan-01's playbook (robocopy `/MIR`, fresh `npm install` from the same lockfile, zero source differences).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `@radix-ui/react-separator` not installed; stock separator needs it but T-05-02-SC bans new packages**
- **Found during:** Task 1
- **Issue:** Stock shadcn `separator.tsx` imports `@radix-ui/react-separator`, which is not in package.json; installing it would violate the plan's own "no new third-party packages" mitigation.
- **Fix:** Wrote `separator.tsx` with the identical stock API (`orientation`, `decorative`, `bg-border` 1px divider) as a dependency-free presentational component; documented the reason in-file.
- **Files modified:** `frontend/components/ui/separator.tsx`
- **Verification:** `tsc --noEmit` exit 0 with the file in-program; how-it-works renders the desktop connector.

**Total deviations:** 1 auto-fixed (blocking). No scope creep — no new features, no new deps.

## Build Evidence (the Phase 5 gate)

```
▲ Next.js 14.2.18
 Creating an optimized production build ...
✓ Compiled successfully
 Linting and checking validity of types ...
 Collecting page data ...
 Generating static pages (0/4) ...
✓ Generating static pages (4/4)
Route (app)  Size     First Load JS
┌ ○ /        18.9 kB  106 kB
└ ○ /_not-found  873 B  88 kB
```

- `npx tsc --noEmit` in the temp tree: exit 0; `--listFiles` confirms all 6 new files are in the typecheck program.
- Full log: `C:/Users/USER/AppData/Local/Temp/wgpt-build-0502/frontend/build-05-02.txt` (robocopy_exit=1 = files-copied-successfully).
- Acceptance greps: 6/6 features strings ✓, 4/4 how-it-works strings ✓, 4/4 teaser strings ✓, Green/Yellow/Orange/Red ×3 + `Alert:` ×4 + `IMD-issued warnings` ✓, `disabled` on chat button + `Arrives in Phase 6` ✓.

## Issues Encountered

- **Stale `.git/index.lock` persists** (same as plan-01): `git add` exit 128, lock unremovable under the H:/ no-delete ACL. Human follow-up unchanged: grant Modify on `H:/weatherGPT`, delete the lock, commit `frontend/` + both plan-01/plan-02 SUMMARies.
- **Next.js 14.2.18 deprecation warning** (known security-vuln notice, same as plan-01): kept the pinned version for D-01 fidelity.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| (none — mitigations shipped) | — | T-05-02-01: disclaimer verbatim in alerts-showcase ✓. T-05-02-02: "Sample values shown" honesty note in teaser ✓. T-05-02-SC: zero new packages (separator deviation above) ✓. No endpoints, auth, or schema changes. |

## Known Stubs

None. Every rendered string is UI-SPEC copy; lorem-grep clean; no TODO/FIXME in the six new files.

## Self-Check

- [x] All 6 files exist on disk in `H:/weatherGPT/frontend/components/`
- [x] `tsc --noEmit` exit 0 (temp tree); `npm run build` exit 0 with log on disk
- [x] No commits to verify (`git add` blocked by stale index.lock — documented, not silent)
- [x] Only plan-listed files touched; backend `.py` files untouched; no `.env` committed

**Result: PASSED** (with environment-blocked git commits explicitly recorded above, per brief).

## Next Phase Readiness

- Plan-03 can import `Features`, `LiveDemoTeaser`, `AlertsShowcase`, `HowItWorks` into `page.tsx` between Hero and the remaining sections (MoES strip, FAQ, footer).
- Human blockers: (1) fix H:/ permissions + stale lock, commit frontend/ + SUMMARies; (2) light/dark + 390px-mobile browser eyeball (rides with plan-03 verification).

---
*Phase: 05-frontend-shell-landing*
*Completed: 2026-09-11*
