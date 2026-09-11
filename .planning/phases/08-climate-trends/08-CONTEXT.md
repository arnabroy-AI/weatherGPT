# Phase 8: Climate trends - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Close the MoES "Climate Information" gap: past-30-day observed aggregates via Open-Meteo archive API behind the IMD-shaped seam, agent grounding for trend questions, compact climate strip on landing. No forecast/current changes, no new providers, v1 scope otherwise locked.

## Implementation Decisions

### Trend source + window
- **D-01:** Open-Meteo archive API (`past_days=30` daily aggregates), same keyless engine. New `get_climate_trends(location: str)` tool returning JSON string.
- **D-02:** 30-day window: rain sum, temp mean/min/max, wettest/driest days, plus deviation note vs the window's own daily means. Same-month-last-year comparison rejected.
- **D-03:** Same disclosure voice (window + non-IMD sourcing in JSON + reply); outage degrades exactly like the current path (stamped mock + disclosed, never silent).

### Agent grounding
- **D-04:** Trend questions route to the new tool; replies cite observed aggregates. Register tool + one prompt rule (Phase 4 minimal-wiring pattern). Mocked-LLM tests proving numbers match fixture.

### Landing surface
- **D-05:** Compact climate strip reusing the alerts-showcase pattern (real copy, zero lorem, tokens unchanged). Chat-only rejected.

### Claude's Discretion
- Exact JSON keys (mirror current style + window fields), strip layout details, anomaly wording.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- `tools/imd_client.py` — fetch/mapping/cache/fallback patterns to extend (archive endpoint, daily aggregates).
- `tools/weather.py` — 18-city map, 10-min cache, fallback + disclosure, frozen current/forecast contracts (untouched).
- `services/agent.py` — `_TOOLS` + one-rule wiring pattern (Phase 3/4 precedent); SYSTEM_PROMPT grounding style.
- `frontend/components/alerts-showcase.tsx` — strip pattern to reuse; `frontend/app/page.tsx` — assembly order.
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (CLIM-01…03), `.planning/ROADMAP.md` (Phase 8 goal + criteria).
- `.planning/phases/02-imd-live-data/02-RESEARCH.md` — provider reference + fixture strategy.

## Existing Code Insights

### Reusable Assets
- `fetch_open_meteo` param/transport/timeout shape — archive call mirrors it (`past_days=30`, `daily=temperature_2m_max,temperature_2m_min,precipitation_sum`).
- `_rainfall_last_24h` aggregation style — window aggregation precedent.
- `set_transport` MockTransport seam + recorded fixtures — trend tests use the same seam, no live CI calls.
- City map + normalization + best-guess — reused as-is for location resolution.

### Established Patterns
- Defensive `.get` parsing, Green-default-style safe defaults, log-full/send-safe, key redaction.
- Disclosure strings in JSON + reply; `source` distinguishes engine/fallback.
- tsc in place; temp-dir builds (H:/ no-delete); pytest guard stays green.

### Integration Points
- New tool function + `@tool` + `_TOOLS` entry + one SYSTEM_PROMPT rule; no route/schema/main changes.
- Climate strip component + `page.tsx` assembly; copy deck real-only, anti-slop bans carry over.

## Specific Ideas

Example judge question from discussion: "was this monsoon wetter than normal in Pune?"

## Deferred Ideas

- Same-month-last-year comparison (rejected for v1). IMD-direct cutover stays a separate track.

---

*Phase: 8-Climate trends*
*Context gathered: 2026-09-11*
