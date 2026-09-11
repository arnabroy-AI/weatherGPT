---
phase: 05-frontend-shell-landing
plan: "03"
subsystem: ui
tags: [nextjs-14, shadcn, tailwindcss, typescript, lucide-react, radix, landing-assembly]
requires: [05-01 (shell, tokens, header/hero tracer), 05-02 (Features, LiveDemoTeaser, AlertsShowcase, HowItWorks)]
provides:
  - Final three landing sections (moes-strip, faq Accordion, footer) with exact UI-SPEC copy
  - Full 8-section page.tsx assembly in D-03 order with header/main/footer landmarks
  - Stock shadcn Accordion/Sheet/DropdownMenu primitives backed by official Radix peers
affects: [phase-06-chat-ui (/chat still reserved, NEXT_PUBLIC_WEATHERGPT_API untouched)]
tech-stack:
  added: [@radix-ui/react-accordion@1.2.20, @radix-ui/react-dialog@1.1.23, @radix-ui/react-dropdown-menu@2.1.24]
  patterns: [single-open collapsible Accordion for FAQ, ghost-Button anchor columns in footer, full-bleed slate band for MoES strip]
key-files:
  created:
    - frontend/components/moes-strip.tsx
    - frontend/components/faq.tsx
    - frontend/components/footer.tsx
    - frontend/components/ui/accordion.tsx
    - frontend/components/ui/sheet.tsx
    - frontend/components/ui/dropdown-menu.tsx
  modified:
    - frontend/app/page.tsx
    - frontend/package.json
    - frontend/package-lock.json
key-decisions:
  - "Installed the three official Radix peers (accordion/dialog/dropdown-menu) so Sheet/DropdownMenu/Accordion are byte-stock shadcn wired to Radix, per plan and UI-SPEC keyboard-native requirement"
  - "Header and theme-toggle left untouched (outside files_modified): existing drawer + segmented Light/Dark/System control already satisfy the responsive/a11y contract; stock Sheet/DropdownMenu ship ready for Phase 6 refinement"
  - "Build proven in C:/Users/USER/AppData/Local/Temp/wgpt-build-0503/frontend (same H:/ no-delete workaround as plans 01/02)"
requirements-completed: [FRNT-01, FRNT-02]
status: complete
---

# Phase 05 Plan 03: MoES Strip + FAQ + Footer Summary

**MoES strip, 6-item Radix Accordion FAQ, and 3-column footer assembled with the 5 prior sections into the full 8-section landing in D-03 order — anti-slop gate clean, build green, backend pytest green.**

## Performance

- **Duration:** ~30 min
- **Tasks:** 3/3 complete
- **Files created:** 6; modified: 3 (page.tsx + package.json/package-lock.json via sanctioned Radix install)

## Accomplishments

- **MoES strip (`MoesStrip`):** full-bleed slate band (`bg-slate-100` / `dark:bg-slate-900`) with 2px amber top border (`border-t-2 border-amber-600 dark:border-amber-400`), SIH26068/MoES-track Badge, H2 "Built for the Ministry of Earth Sciences (SIH26068)", Separator rule, and the verbatim data-roadmap paragraph (keyless model engine today with honest disclosure → IMD-direct next). Zero `img`/logo tags, zero endorsement claims (T-05-03-01).
- **FAQ (`Faq`, `id="faq"`):** narrow `max-w-3xl` single-open collapsible Accordion (`type="single" collapsible`) with exactly the six UI-SPEC Q&A (data source + IMD-issued-warnings disclosure, under-5-seconds fallback, 18 mapped cities + best-guess disclosure, six crops, Hindi-v2, POST /api/chat + GET /health). Keyboard-native via Radix, glass-card container, Inter 16px answers.
- **Footer (`Footer`, `<footer>` landmark):** brand cell (wordmark + amber-bordered SIH Badge), Product column (Features, Live demo, Alerts, How it works → in-page anchors via ghost Buttons), Project column (SIH26068, MoES track, API docs, Status: v1 demo), Fine print ("Demo build — forecasts are model estimates, not official IMD warnings. For official warnings follow IMD."), Separator above bottom bar ("© 2026 WeatherGPT · SIH26068" + "English-first · No accounts in v1").
- **Page assembly (`app/page.tsx`):** Header + Hero + Features + LiveDemoTeaser + AlertsShowcase + HowItWorks + MoesStrip + Faq inside `<main id="main-content">`, Footer after — exactly the D-03 order, with `aria-labelledby` on every section and a single page H1 (hero only).
- **Stock primitives:** `ui/accordion.tsx`, `ui/sheet.tsx` (44px close control, focus-visible teal ring), `ui/dropdown-menu.tsx` — byte-stock shadcn backed by `@radix-ui/react-accordion@1.2.20`, `@radix-ui/react-dialog@1.1.23`, `@radix-ui/react-dropdown-menu@2.1.24` (official scope, same publisher as pre-existing `@radix-ui/react-slot`; npm registry only, no third-party registries — T-05-03-SC).
- **Full verification gate (Task 3):** lorem=0, gradient markers=0, `<img`=0, `href="/chat"`=0, h1 count=1, no `frontend/app/chat` dir, domain copy in every new section file, 20 a11y-marker hits, 74 responsive-class hits, 6 light/dark token hits; prerendered HTML contains all 8 section anchors in strictly increasing document order; `npm run build` exit 0; `python -m pytest tests/ -q` → 76 passed, 1 skipped.

## Task Commits

Per-task commits were **not possible**: `git add`/`git commit` fail with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (stale lock, same as plans 01/02; exit 128; lock unremovable under the H:/ no-delete ACL). Per the execution brief, git was best-effort and non-blocking. No `.env` touched or staged.

1. **Task 1: MoES strip + FAQ + footer** — uncommitted (files on disk, `tsc --noEmit` exit 0)
2. **Task 2: Page assembly + nav primitives** — uncommitted (files on disk, `tsc --noEmit` exit 0)
3. **Task 3: Verification gate** — verification only, no file changes needed (gate clean first pass)

## Files Created/Modified

- `frontend/components/moes-strip.tsx` — MoES statement band (created)
- `frontend/components/faq.tsx` — 6-item Accordion, id faq (created)
- `frontend/components/footer.tsx` — 3 columns + bottom bar (created)
- `frontend/components/ui/accordion.tsx`, `frontend/components/ui/sheet.tsx`, `frontend/components/ui/dropdown-menu.tsx` — stock shadcn (created)
- `frontend/app/page.tsx` — 8-section D-03 assembly (modified: replaced Header+Hero tracer composition)
- `frontend/package.json`, `frontend/package-lock.json` — modified by the sanctioned Radix-peer install only (3 new deps, no removals)
- Backend untouched (no `.py` opened for writing); no `/chat` route; no `.env` changes

## Decisions Made

- Installed the three Radix peers instead of hand-rolling presentational fallbacks (plan-02's separator precedent did not apply): the plan and UI-SPEC explicitly require Radix-wired, keyboard-native Accordion/Sheet/DropdownMenu, and T-05-03-SC sanctions stock shadcn.
- Did not rewire header.tsx/theme-toggle.tsx to Sheet/DropdownMenu: both files are outside this plan's `files_modified`, and the existing controls already meet the contract (hamburger `md:hidden` + links `md:flex` at 768px, `aria-expanded`, `aria-pressed` on Light/Dark/System, 44px touch targets). Stock Sheet/DropdownMenu ship import-ready for Phase 6.
- Temp-dir build proof reused from the plan-01/02 playbook (robocopy `/MIR` excluding `node_modules`/`.next`, fresh `npm install` from the updated lockfile, zero source differences).

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written. Two boundary notes (not deviations):

1. **Header keeps its plan-01 drawer instead of stock Sheet.** Task 2 action text names Sheet for the mobile drawer, but header.tsx is outside `files_modified` and the orchestrator boundary ("touch ONLY your plan's files_modified") takes precedence. Behavior contract still met — evidence in Responsive Evidence below. Stock Sheet exists for Phase 6 to adopt.
2. **Theme switcher keeps its segmented control instead of DropdownMenu.** Same boundary reason; `aria-pressed` Light/Dark/System control already satisfies UI-SPEC. Stock DropdownMenu exists for Phase 6.

## Build Evidence (the Phase 5 gate)

```
▲ Next.js 14.2.18
 Creating an optimized production build ...
✓ Compiled successfully
 Linting and checking validity of types ...
 Collecting page data ...
 Generating static pages (0/4) ...
✓ Generating static pages (4/4)
Route (app)                              Size     First Load JS
┌ ○ /                                    27 kB           114 kB
└ ○ /_not-found                          873 B            88 kB
```

- `npx tsc --noEmit` on `H:/weatherGPT/frontend`: exit 0 (zero type errors on the committed tree itself).
- Full log: `C:/Users/USER/AppData/Local/Temp/wgpt-build-0503/frontend/build-05-03.txt`.
- Prerendered `.next/server/app/index.html`: FOUND `id="top"`, `id="features"`, `id="live-demo"`, `id="alerts"`, `id="how-it-works"`, `Ministry of Earth Sciences`, `id="faq"`, `2026 WeatherGPT`, H1 "Ask the weather in plain words" — offsets strictly increasing (7348 < 12146 < 18548 < 23561 < 26871 < 29222 < 30291 < 39297), proving D-03 document order.
- Backend guard: `python -m pytest tests/ -q` → **76 passed, 1 skipped in 10.38s**.

## Anti-Slop Evidence (Task 3 gate)

| Check | Command scope | Result |
|-------|---------------|--------|
| Zero lorem | case-insensitive `lorem` over app/components/lib `*.tsx/*.ts/*.css` | **0 matches** |
| No purple-blue gradients | `from-purple\|via-blue\|purple-500\|blue-500\|linear-gradient` over same scope | **0 matches** (only teal `radial-gradient` hero wash in globals.css) |
| No clipart | `<img` over app + components `*.tsx` | **0 matches** (lucide icons + CSS shapes only) |
| No dead chat links | `href="/chat"` over app/components/lib | **0 matches**; `frontend/app/chat` does not exist |
| Single H1 | `<h1` over page.tsx + hero.tsx; `<h1[^a-z]` over app + components | **1 total** (hero H1); zero elsewhere |
| Domain copy | `IMD\|Alert\|monsoon\|forecast\|crop\|district\|Ministry\|SIH26068\|/api/chat\|/health` over 3 new files | hits in every file (e.g. moes-strip: Ministry + SIH26068 + IMD-direct; faq: IMD-issued warnings + crop notes + POST /api/chat; footer: SIH26068 + not official IMD + 2026 WeatherGPT) |
| No stubs | `TODO\|FIXME\|placeholder\|coming soon\|not available` over 7 plan files | **0 matches** |

## Responsive Evidence (390px + light/dark, Task 3 gate)

- **Light/dark tokens:** globals.css carries `#0f7667` + `#d97706` (light) and `#2dd4bf` + `#fbbf24` (dark) plus `radial-gradient` hero wash and `prefers-reduced-motion` kill-switch (6 token hits).
- **390px rules by class assertion:** 74 hits across app + components for `md:hidden` (hamburger), `md:flex` (nav links ≥768px), `grid-cols-1` (1-col base grids), `flex-col` + `sm:flex-row`/`sm:w-auto` (CTAs stack full-width `w-full` at 390px), `max-w-6xl` containers with `px-4` gutters, and stock `Sheet` (drawer primitive present).
- **Touch/a11y:** icon-only controls ≥44px (`h-11 w-11` hamburger, Sheet close), 20 a11y-marker hits (`focus-visible` teal rings, `aria-labelledby` per section, `aria-pressed` theme states, skip link, `prefers-reduced-motion`).
- **Held for human eyes:** light/dark render of all 8 sections and 390px overlap eyeball in a real browser (no browser automation in this environment). File/content evidence above is the machine-checkable half; visual sign-off rides with `/gsd-verify-work`.

## Issues Encountered

- **Stale `.git/index.lock` persists** (same as plans 01/02): `git status` reads fine but `git add`/`git commit` exit 128; lock unremovable under the H:/ no-delete ACL. Human follow-up unchanged: grant Modify on `H:/weatherGPT`, delete the lock, commit `frontend/` + all three plan SUMMARies.
- **PowerShell 5.1 notes:** `Select-String` has no `-Recurse` (used `Get-ChildItem -Recurse | Select-String`, excluding `node_modules`/`.next` to avoid timeouts); `&&` unsupported (used `; if ($?)` chains).
- **Next.js 14.2.18 deprecation warning** (known security-vuln notice, same as plans 01/02): kept the pinned version for D-01 fidelity.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| (none — mitigations shipped) | — | T-05-03-01: no logos/endorsement claims; footer fine print states model estimates are not official IMD warnings ✓. T-05-03-02: `.env.local.example` untouched (placeholder URL only, pre-existing) ✓. T-05-03-SC: stock shadcn only; 3 new packages all in the official `@radix-ui` scope (accordion 1.2.20, dialog 1.1.23, dropdown-menu 2.1.24), same publisher as pre-existing `@radix-ui/react-slot` ✓. No endpoints, auth, or schema changes. |

## Known Stubs

None. Every rendered string is UI-SPEC copy; stub-pattern grep clean (0 matches).

## Self-Check

- [x] All 7 plan files exist on disk (`moes-strip.tsx`, `faq.tsx`, `footer.tsx`, `ui/accordion.tsx`, `ui/sheet.tsx`, `ui/dropdown-menu.tsx`, `app/page.tsx`)
- [x] `tsc --noEmit` exit 0 on H:/ tree; `npm run build` exit 0 in temp tree with log on disk; prerendered HTML order proof
- [x] `python -m pytest tests/ -q` → 76 passed, 1 skipped (backend untouched, still green)
- [x] No commits to verify (`git add` blocked by stale index.lock — documented, not silent)
- [x] Only plan-listed files created/modified (+ package.json/lock via sanctioned install); no `.env` touched; no `/chat` route

**Result: PASSED** (with environment-blocked git commits explicitly recorded above, per brief).

## Next Phase Readiness

- Landing is complete: 8 sections in D-03 order, both suites green, `/chat` reserved. Phase 6 can mount the chat UI on this shell and consume `NEXT_PUBLIC_WEATHERGPT_API`.
- Human blockers: (1) fix H:/ permissions + stale lock, commit `frontend/` + plan-01/02/03 SUMMARies; (2) light/dark + 390px-mobile browser eyeball (recorded above as held checklist items).

---
*Phase: 05-frontend-shell-landing*
*Completed: 2026-09-11*
