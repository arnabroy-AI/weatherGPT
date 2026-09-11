# Phase 5: Frontend shell + landing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 5-Frontend shell + landing
**Areas discussed:** Framework setup, Landing IA, Design tokens, Anti-slop bar

---

## Framework setup

| Option | Description | Selected |
|--------|-------------|----------|
| Next.js + shadcn | Next.js 14 App Router + TS + Tailwind in frontend/ | ✓ |
| Vite + shadcn | Lighter, no SSR | |

**User's choice:** Next.js + shadcn

| Option | Description | Selected |
|--------|-------------|----------|
| Stock shadcn | components/ui, lib/utils, CSS-variable theme | ✓ |
| Minimal custom | Hand-picked components | |

**User's choice:** Stock shadcn

---

## Landing IA

| Option | Description | Selected |
|--------|-------------|----------|
| Roadmap 8 | hero, features, demo teaser, alerts, how-it-works, MoES strip, FAQ, footer | ✓ |
| Trimmed 5 | hero, features, demo teaser, FAQ, footer | |

**User's choice:** Roadmap 8

| Option | Description | Selected |
|--------|-------------|----------|
| Real copy now | From API copy + MoES/IMD facts, zero lorem | ✓ |
| Draft placeholders | Review before Phase 6 | |

**User's choice:** Real copy now

---

## Design tokens

| Option | Description | Selected |
|--------|-------------|----------|
| Teal + amber | Deep teal + warm amber on slate glass, light + dark | ✓ |
| IMD blue | Blue + green, light first | |

**User's choice:** Teal + amber

| Option | Description | Selected |
|--------|-------------|----------|
| Grotesk + Inter | Space Grotesk display + Inter body via next/font | ✓ |
| Inter only | Single family | |

**User's choice:** Grotesk + Inter

---

## Anti-slop bar

| Option | Description | Selected |
|--------|-------------|----------|
| Ban list + review | Explicit bans + visual review checklist | ✓ |
| Trust tokens | No explicit gate | |

**User's choice:** Ban list + review

---

## Agent's Discretion

- Component boundaries, token hex values, blur/radius scale, toggle placement.

## Deferred Ideas

- Chat UI + wiring → Phase 6; deploy → Phase 7.
