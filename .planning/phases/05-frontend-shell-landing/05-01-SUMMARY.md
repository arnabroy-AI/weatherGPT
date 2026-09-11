---
phase: 05-frontend-shell-landing
plan: "01"
subsystem: ui
tags: [nextjs-14, tailwindcss, shadcn, typescript, next-font, next-themes, glassmorphism]

# Dependency graph
requires: []
provides:
  - Greenfield frontend/ shell: Next.js 14 App Router + TS + Tailwind + stock shadcn layout
  - Glassmorphism token system (teal + amber on slate glass, light + dark) with Space Grotesk + Inter
  - Tracer slice: sticky glass header + hero with exact UI-SPEC copy, proven by a green production build
affects: [05-frontend-shell-landing plans 02-03 (7 expansion sections), phase-06-chat-ui (NEXT_PUBLIC_WEATHERGPT_API + /chat reservation)]

# Actuals — pairs with the plan's `estimate` (same chars/4 scale over realized diff)
actuals:
  tokens: 9000
  tasks: 3
  commits: 0

# Tech tracking
tech-stack:
  added: [next@14.2.18, react@18.3.1, tailwindcss@3.4, typescript@5.6, lucide-react, clsx, tailwind-merge, class-variance-authority, next-themes@0.3, @radix-ui/react-slot, tailwindcss-animate]
  patterns: [shadcn stock layout (components/ui + lib/utils + CSS-variable theme), class-based dark mode via next-themes, next/font with CSS variables]

key-files:
  created:
    - frontend/app/layout.tsx
    - frontend/app/page.tsx
    - frontend/app/globals.css
    - frontend/components/header.tsx
    - frontend/components/hero.tsx
    - frontend/components/theme-toggle.tsx
    - frontend/components/ui/button.tsx
    - frontend/components/ui/badge.tsx
    - frontend/lib/utils.ts
  modified: []

key-decisions:
  - "Hand-scaffolded the stock shadcn layout (plan-sanctioned fallback) instead of running npx shadcn init, for a deterministic result"
  - "next-themes ThemeProvider with Light/Dark/System, defaulting to prefers-color-scheme"
  - "Mobile nav as a minimal local drawer (plan allows it: only button+badge primitives installed in this tracer)"
  - "Production build proven in a full-control temp dir (C:/Users/USER/AppData/Local/Temp/opencode/wgpt-build) because H:/ denies file deletion, which breaks Next.js build renames"

patterns-established:
  - "Glass utilities: .glass-card (blur-md), .glass-header (blur-sm), .glass-hero-panel (blur-lg) over CSS-variable tokens"
  - "Kicker style: Inter 14px/600/uppercase/+0.08em in amber; hero display clamp(32px,5vw,40px) Space Grotesk 600"
  - "Page container max-w-6xl, 16px mobile / 24px desktop gutters, 64px mobile / 96px desktop section rhythm"

requirements-completed: [FRNT-01, FRNT-02]

# Coverage metadata — deterministic UAT routing for verify-work
coverage:
  - id: D1
    description: "Stock Next.js 14 + shadcn scaffold (package.json, components.json, cn helper, reserved env name, zero chat files)"
    requirement: "FRNT-01"
    verification:
      - kind: other
        ref: "node --version => v24.13.0; npm --version => 11.12.1; Select-String NEXT_PUBLIC_WEATHERGPT_API in .env.local.example => match; chat-file search => zero matches"
        status: pass
    human_judgment: false
  - id: D2
    description: "Token system + fonts + Light/Dark/System theme (teal/amber tokens, Grotesk + Inter, skip link, focus rings, reduced-motion)"
    requirement: "FRNT-01"
    verification:
      - kind: other
        ref: "globals.css contains #0f7667 + #d97706, zero linear-gradient matches; layout.tsx uses next/font Space_Grotesk + Inter; theme-toggle.tsx offers Light/Dark/System"
        status: pass
    human_judgment: false
  - id: D3
    description: "Tracer header + hero with exact UI-SPEC copy; root route prerenders end-to-end; production build green with zero type errors"
    requirement: "FRNT-02"
    verification:
      - kind: other
        ref: "npm run build exit 0 (full route table, 4/4 static pages); npx tsc --noEmit exit 0; prerendered .next/server/app/index.html contains H1 + id=top; lorem grep across app/components/lib => 0 matches"
        status: pass
    human_judgment: false
  - id: D4
    description: "Visual sign-off: light + dark render of header/hero and 390px mobile stacked-CTA + drawer check in a real browser"
    verification: []
    human_judgment: true
    rationale: "No browser automation available in this environment — requires a human to open the dev server and eyeball both modes plus mobile width"

# Metrics
duration: ~70min
completed: 2026-09-11
status: complete
---

# Phase 05 Plan 01: Frontend Shell Tracer Summary

**Stock Next.js 14 + shadcn scaffold with teal/amber glass tokens, Grotesk + Inter, and a header/hero tracer slice — production build green with zero type errors.**

## Performance

- **Duration:** ~70 min (02:45–03:55 UTC, 2026-09-11; dominated by ~50 min fighting environment file-lock/build-hang issues — see Issues Encountered)
- **Started:** 2026-09-11T02:45Z
- **Completed:** 2026-09-11T03:55Z
- **Tasks:** 3/3 complete
- **Files created:** 18 source files (+ package-lock.json); 0 modified (greenfield)

## Toolchain (Task 1 verify)

- **node:** v24.13.0
- **npm:** 11.12.1
- Both present; versions recorded per plan environment notes.

## Accomplishments

- Scaffolded greenfield `frontend/` per D-01/D-02: Next.js 14.2.18 App Router (no src/ dir), TypeScript strict, Tailwind 3.4, stock shadcn layout (`components.json` slate base + `cssVariables: true`, `components/ui`, `lib/utils.ts` with `cn`), `button` + `badge` stock primitives with Radix Slot peer.
- Reserved `NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000` in `frontend/.env.local.example` for Phase 6; **no `/chat` route and no chat files exist** (verified by recursive filename search — zero matches).
- Implemented the UI-SPEC token system exactly (D-05/D-06): slate-50/slate-950 page, glass fills/borders, blur scale (header sm / cards md / hero panel lg), `rounded-2xl` cards / 10px buttons / full chips, light + dark shadows, hero-only teal radial wash (`radial-gradient`, **no `linear-gradient` anywhere** — grep-verified), teal `#0f7667` / amber `#d97706` (+ dark `#2dd4bf` / `#fbbf24`).
- Loaded Space Grotesk 600 (display) + Inter 400/600 (body) via `next/font` with display-swap and CSS variables; 2px teal `:focus-visible` rings; skip-to-content link; `prefers-reduced-motion` disables the wash; Light/Dark/System switcher defaulting to system.
- Shipped the tracer slice end-to-end (D-03/D-04/D-07): sticky glass header (WeatherGPT wordmark, Features/Live demo/Alerts/How it works/FAQ links, theme switcher, "Try a sample question" CTA, hamburger drawer <768px) + hero `#top` with the exact UI-SPEC copy (SIH26068 eyebrow, H1 "Ask the weather in plain words. Get answers India can act on.", dual CTAs to `#live-demo` / `#how-it-works`, microcopy, 18-cities/5-day/4-levels metric row, keyless-engine trust line). Lucide icons only, zero lorem (case-insensitive grep over app/components/lib: **0 matches**).
- **Build gate GREEN:** `npm run build` exit 0 — Compiled successfully, lint + type check passed, 4/4 static pages, route table (`/` 18.9 kB / 106 kB first load). `npx tsc --noEmit` exit 0 separately. Prerendered `.next/server/app/index.html` contains the H1, `id="top"`, and full header/hero markup — the single happy path renders from tokens end-to-end.
- Backend Python tree untouched (only `frontend/` files created; repo has no commits yet so there is nothing to diff, and no `.py` file was opened for writing).

## Task Commits

Per-task commits were **not possible**: `git add` fails with `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists` (stale lock), and the lock file itself cannot be removed because the `H:/` filesystem denies file deletion to this user (see Issues Encountered). Per the execution brief, git was best-effort and non-blocking.

1. **Task 1: Verify toolchain + scaffold** — uncommitted (files on disk)
2. **Task 2: Tokens + fonts + theme** — uncommitted (files on disk)
3. **Task 3: Tracer header + hero** — uncommitted (files on disk)

**Plan metadata:** no docs commit (same git blockage; `.planning/` is also untracked in this fresh repo).

## Files Created/Modified

- `frontend/package.json` — pinned deps (next 14.2.18, react 18, tailwind 3.4, lucide-react, cva/clsx/tailwind-merge, next-themes, radix slot)
- `frontend/package-lock.json` — generated by npm install (version pins for T-05-01-01/T-05-01-SC)
- `frontend/next.config.mjs` — stock Next config (JSDoc-typed; see deviation 1)
- `frontend/tailwind.config.ts` — shadcn stock theme (class dark mode, CSS-var colors, container max-w-6xl/1152px)
- `frontend/tsconfig.json` — stock Next TS config with `@/*` paths
- `frontend/postcss.config.mjs` — tailwind + autoprefixer
- `frontend/components.json` — stock shadcn (default style, slate base, cssVariables true, lucide)
- `frontend/.env.local.example` — `NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000` + Phase 6 comment
- `frontend/.gitignore` — node_modules, .next, build, env locals, tsbuildinfo
- `frontend/lib/utils.ts` — `cn` helper
- `frontend/app/layout.tsx` — fonts, ThemeProvider, skip link, metadata
- `frontend/app/globals.css` — full token system + glass utilities + a11y base
- `frontend/app/page.tsx` — tracer composition: Header + Hero only
- `frontend/components/header.tsx` — sticky glass header + mobile drawer
- `frontend/components/hero.tsx` — hero with exact UI-SPEC copy
- `frontend/components/theme-toggle.tsx` — Light/Dark/System switcher
- `frontend/components/ui/button.tsx`, `frontend/components/ui/badge.tsx` — stock shadcn primitives (teal default button)
- Generated (gitignored, not deliverables): `frontend/next-env.d.ts`, `frontend/tsconfig.tsbuildinfo`, `frontend/.next/`, `frontend/build-*.txt`, `frontend/tsc-check.txt`

## Decisions Made

- Hand-scaffolded the stock shadcn layout (plan-sanctioned fallback) rather than `npx shadcn init`: npm registry access worked, but hand-scaffolding gave a byte-deterministic stock result (slate base, CSS variables, class dark mode) with no interactive CLI risk.
- Theme via `next-themes` (the stock shadcn approach) with a segmented Light/Dark/System control carrying `aria-pressed` states.
- Mobile nav as a minimal local `useState` drawer, explicitly permitted by the plan for this tracer (only button+badge installed; full Sheet arrives with plan 02/03 scope if needed).
- Build proven in `C:/Users/USER/AppData/Local/Temp/opencode/wgpt-build/frontend` (byte-identical source copy via robocopy, fresh `npm install` from the same lockfile) because `H:/` denies deletion — see Issues Encountered. No source differences between proven tree and committed tree (copy excluded only `node_modules`, `.next`, local logs).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `next.config.mjs` contained TypeScript syntax (`import type`), crashing the build**
- **Found during:** Task 2 (first `npm run build`)
- **Issue:** `Failed to load next.config.mjs ... SyntaxError: Unexpected token '{'` — `.mjs` is parsed as plain JS, so `import type` is illegal.
- **Fix:** Rewrote as JSDoc-typed plain JS (`/** @type {import('next').NextConfig} */`).
- **Files modified:** `frontend/next.config.mjs`
- **Verification:** Subsequent builds parse config successfully (reached "Compiled successfully").

**2. [Rule 3 - Blocking] Production build cannot complete on `H:/` — proved it on an identical tree in a full-control temp dir**
- **Found during:** Tasks 2–3 (build gate)
- **Issue:** `npm run build` on `H:/weatherGPT/frontend` repeatedly (a) failed with `EPERM ... rename` on webpack cache / `export/500.html → server/pages/500.html`, then (b) hung post-export with zero fs writes for 35+ min while burning CPU. Root cause (icacls evidence): the user has only RX+W (no Delete) under `H:/`, and Next.js build relies on file renames/deletes.
- **Fix:** `robocopy`ed the source tree (excluding `node_modules`/`.next`/logs) to `C:/Users/USER/AppData/Local/Temp/opencode/wgpt-build/frontend`, ran `npm install` (25 s, clean) + `npm run build` there → **exit 0**. No build-config changes; no source differences.
- **Verification:** Exit code 0 + full route table + prerendered HTML grep hits (see Build Evidence below).

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both required for the build gate; no scope creep — no new features, no new deps, no architecture change.

## Build Evidence (the Phase 5 gate)

```
> weathergpt-frontend@0.1.0 build
> next build
  ▲ Next.js 14.2.18
   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/4) ...
 ✓ Generating static pages (4/4)
   Finalizing page optimization ...
   Collecting build traces ...
Route (app)                              Size     First Load JS
┌ ○ /                                    18.9 kB         106 kB
└ ○ /_not-found                          873 B            88 kB
+ First Load JS shared by all            87.1 kB
○  (Static)  prerendered as static content
build-exit:0
```

- `npx tsc --noEmit` in `H:/weatherGPT/frontend`: exit 0 (zero type errors on the committed tree itself).
- Full log: `C:/Users/USER/AppData/Local/Temp/opencode/wgpt-build/frontend/build-evidence.txt`.
- Acceptance greps: `NEXT_PUBLIC_WEATHERGPT_API` in `.env.local.example` ✓; `#0f7667` + `#d97706` in `globals.css` ✓; `linear-gradient` in `globals.css` → no matches ✓; `lorem` (ci) across app/components/lib → 0 ✓; `SIH26068` + `18 cities mapped` in `hero.tsx` ✓; `WeatherGPT` + drawer trigger in `header.tsx` ✓; chat filename search → zero ✓; `Ask the weather in plain words` + `id="top"` in prerendered `index.html` ✓ (page.tsx composes Header+Hero, so the literal strings live in `hero.tsx` — intent verified at the rendered-route level).

## Issues Encountered

- **H:/ denies file deletion (ACL: Authenticated Users = RX,W only):** `npm install` EPERM warnings, `next build` EPERM renames + post-export hang, `.next`/log cleanup impossible, stale `.git/index.lock` unremovable → `git add` exit 128. None of these reflect the code; all are environment filesystem permissions. Mitigated via the temp-dir build; everything else documented. **Follow-up for the human:** run the next build/dev from a directory the user owns, or have an admin grant Modify on `H:/weatherGPT`; then remove the stale `.git/index.lock` and commit `frontend/` + this SUMMARY.
- **Next.js 14.2.18 deprecation warning** (`npm warn deprecated ... security vulnerability, upgrade to a patched version`): kept the plan-pinned 14.2.18 for D-01 fidelity. Recommend plans 02/03 bump to the patched 14.2.x.
- **Stdout swallowing:** `next build` printed nothing past the banner when output was redirected on this machine (even on successful stages); the foreground TTY-less pipe in the very first attempt did stream. Evidence was therefore taken from exit codes, artifact inspection, and teed files — not from watched progress lines.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| (none — no new surface) | — | No endpoints, auth paths, or schema changes. Only stock-registry deps installed (`next`, `react`, `tailwindcss`, `lucide-react` — all verified present on npmjs via successful install of exact pinned versions in `package-lock.json`); no third-party shadcn registries used. Hero trust line states the keyless-model engine honestly with no MoES/IMD endorsement claims or logos (T-05-01-02). |

## Known Stubs

None. Every rendered string is real UI-SPEC copy; no TODO/FIXME/placeholder text in `frontend/app` or `frontend/components` (lorem-grep clean).

## User Setup Required

None - no external service configuration required. (Phase 6 will need `.env.local` with `NEXT_PUBLIC_WEATHERGPT_API`, already reserved in `.env.local.example`.)

## Self-Check

- [x] `frontend/app/layout.tsx`, `page.tsx`, `globals.css`, `header.tsx`, `hero.tsx` exist on disk
- [x] `tsc --noEmit` exit 0; `npm run build` exit 0 (temp-dir proof of identical tree); prerendered H1 proof
- [x] No commits exist to verify (repo has zero commits; `git add` blocked by stale `index.lock` + no-delete ACL — documented, not silent)
- [x] Backend `.py` files untouched (no writes outside `frontend/` + this SUMMARY)

**Result: PASSED** (with the environment-blocked git commits explicitly recorded above, per brief).

## Next Phase Readiness

- Shell, tokens, fonts, theme, and header/hero tracer are proven — plans 02-03 can add the remaining 7 sections on this slice.
- Blockers for the human: (1) fix `H:/` write permissions + delete stale `.git/index.lock`, then commit `frontend/` and this SUMMARY; (2) visual light/dark + 390px-mobile browser check (coverage D4) — can ride along with plan 02/03 verification.

---
*Phase: 05-frontend-shell-landing*
*Completed: 2026-09-11*
