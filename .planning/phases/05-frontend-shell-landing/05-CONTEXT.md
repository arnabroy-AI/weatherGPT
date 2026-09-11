# Phase 5: Frontend shell + landing - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Greenfield frontend in `frontend/`: Next.js 14 App Router + TS + Tailwind + stock shadcn setup, glassmorphism SaaS design system (teal + amber, Grotesk + Inter, light + dark), full 8-section landing with real copy. No chat wiring (Phase 6), no backend changes.

## Implementation Decisions

### Framework setup
- **D-01:** Next.js 14 App Router + TypeScript + Tailwind CSS + shadcn, rooted at `frontend/`.
- **D-02:** Stock shadcn CLI layout (`components/ui`, `lib/utils`, CSS-variable theme). No custom-minimal variant.

### Landing IA
- **D-03:** All 8 roadmap sections in order: hero, features, live-demo teaser, alerts showcase, how-it-works, MoES/IMD strip, FAQ, footer.
- **D-04:** Real copy now — written from backend API copy + MoES/IMD facts. Zero lorem ipsum anywhere.

### Design tokens
- **D-05:** Palette: deep teal + warm amber accents over slate glass. Light + dark modes both first-class.
- **D-06:** Typography: Space Grotesk (display) + Inter (body) via `next/font`. Tight tracking on display sizes.

### Anti-slop bar
- **D-07:** Explicit ban list enforced + visual review checklist at verification: no purple-blue gradients, no robot/AI clipart, no lorem ipsum, no generic undifferentiated cards. Every section must carry real content and WeatherGPT-specific voice.

### Claude's Discretion
- Component boundaries within sections, exact token hex values, glass blur/radius scale, dark-mode toggle placement.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- Backend API (frozen, read-only reference): `POST {base}/api/chat → {reply, alert_level}`; `GET {base}/health`. No backend edits in Phase 5.
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (FRNT-01, FRNT-02), `.planning/ROADMAP.md` (Phase 5 goal + 4 criteria).
- UI-SPEC: `/gsd-ui-phase 5` SHOULD run before planning (roadmap UI hint). If present, `05-UI-SPEC.md` in this phase dir is authoritative for layout/tokens.

### Project scope
- No `frontend/` exists yet — greenfield. Backend phases 1–4 are the API contract; do not modify Python code.

## Existing Code Insights

### Reusable Assets
- Backend alert levels (Green/Yellow/Orange/Red) + `Alert:` line format — the alerts-showcase section previews the same four states the chat will badge in Phase 6.
- Disclosure/source strings (`open-meteo-live…`, `mock-imd-fallback`) — live-demo teaser copy must echo honest data sourcing.
- Copy sources: tool advisories (`tools/imd_client.py` `_build_advisory`), agri notes (`services/agri_advisories.py`), README-style API descriptions.

### Established Patterns
- Stock shadcn conventions only — no custom component framework. Tailwind CSS variables for theming (light/dark via class).
- `NEXT_PUBLIC_*` env convention for the backend base URL (consumed in Phase 6; define the variable name now so both phases agree: `NEXT_PUBLIC_WEATHERGPT_API`).

### Integration Points
- Phase 6 will mount the chat UI on this shell and call the backend via `NEXT_PUBLIC_WEATHERGPT_API` — landing must reserve the `/chat` (or agreed) route for it; do not build chat now.
- `npm run build` with zero type errors is the Phase 5 gate — keep the dependency set minimal and pinned.

## Specific Ideas

Palette anchor from discussion: deep teal + warm amber on slate glass. Type pairing: Space Grotesk + Inter.

## Deferred Ideas

- Chat UI + backend wiring → Phase 6. Alert badges interactive behavior → Phase 6. Docker/frontend deploy → Phase 7.

---

*Phase: 5-Frontend shell + landing*
*Context gathered: 2026-09-11*
