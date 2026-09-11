# Phase 3: Forecast + alerts - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Add 5-day day-wise forecast (min/max, rain chance, condition, per-day alert) plus worst-day `Alert:` line and advisories — through the tool/data layer. Current-weather tool, cache, fallback, city map, agent orchestration, and UI are out of scope except the minimal wiring noted below.

## Implementation Decisions

### Forecast shape
- **D-01:** New `get_weather_forecast(location: str)` tool; `get_current_weather` untouched. Open-Meteo `daily=` API behind the same IMD-shaped seam.
- **D-02:** 5 days; per day: date, min/max °C, rain chance %, condition text, per-day alert level. Same disclosure strings as current path (non-IMD model data).

### Alert authority
- **D-03:** Reuse the existing `derive_alert_level` heuristic per forecast day — no separate stricter thresholds.
- **D-04:** Multi-day replies carry ONE `Alert:` line with the worst day in range, e.g. `Alert: Orange (Sat)`. Existing single-day format unchanged.
- **D-05:** Advisories: per-day text for each Orange/Red day PLUS one overall trip-level rollup line.

### Cache + fallback
- **D-06:** Same 10-minute in-memory cache, keyed `location + days`. No separate TTL.
- **D-07:** Forecast outage → partial current-only payload + honest "forecast unavailable" note. No full mock forecast bundle.

### Agent boundary
- **D-08:** Minimal wiring only: register the new tool on the agent + one-line prompt rule for when to call it. Full forecast orchestration (location resolution, agri/climate) belongs to Phase 4.

### Claude's Discretion
- Exact forecast JSON key names (mirror current-payload style), rollup-line wording, days-parameter handling.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- `tools/imd_client.py` — fetch/mapping/`derive_alert_level`/advisory patterns to extend (daily fields, per-day alerts).
- `tools/weather.py` — 10-min cache, fallback + disclosure, 18-city map, frozen 14-key current contract.
- `services/agent.py` — tool registration + SYSTEM_PROMPT (minimal wiring only); 30s retry/threadpool untouched.
- `api/routes.py`, `schemas/chat.py`, `main.py`, `core/config.py` — unchanged in Phase 3.
- `.planning/phases/02-imd-live-data/02-RESEARCH.md` — Open-Meteo field reference + fixture strategy.
- `.planning/phases/02-imd-live-data/COVERAGE.md` — forecasts OPT-OUT'd to Phase 3; Phase 3 INTEGRATEs them (update the matrix).

### Project scope
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (ALRT-01…ALRT-03), `.planning/ROADMAP.md` (Phase 3 goal + criteria).
- `.planning/phases/02-imd-live-data/02-CONTEXT.md` — D-01…D-09 carry over.

## Existing Code Insights

### Reusable Assets
- `fetch_open_meteo` param pattern — add `daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode` alongside current.
- `derive_alert_level(code, wind, rain)` — callable per forecast day (daily wind/rain sums where available).
- `_build_advisory` per-level texts — reuse for per-day advisories; rollup is new.
- `set_transport`/`reset_transport` MockTransport seam — forecast tests use the same seam + recorded daily fixture.
- Phase 1 `_derive_alert_level` reply parser — worst-day line format must still match `Alert: <level>` regex (day tag in parens after).

### Established Patterns
- Defensive `.get` parsing, Green default, log-full/send-safe, key redaction — all apply to the daily path.
- MockTransport + fixtures only in CI; deterministic placeholders on outage.
- Cache keyed by normalized location — extend key with day count.

### Integration Points
- New tool module function + `@tool` registration; agent `_TOOLS` list gains one entry + one prompt line.
- `source` strings distinguish live/forecast/fallback; staleness fields mirror current path.

## Specific Ideas

Example worst-day line from discussion: `Alert: Orange (Sat)`.

## Deferred Ideas

None — agent orchestration → Phase 4; UI badges → Phase 6.

---

*Phase: 3-Forecast + alerts*
*Context gathered: 2026-09-11*
