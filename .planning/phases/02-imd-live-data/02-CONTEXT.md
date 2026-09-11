# Phase 2: IMD live data - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Replace the mock body of `get_current_weather` with real IMD current-weather data, keeping the frozen contract `get_current_weather(location: str) -> JSON string` (same keys, same tool name). Add a 10-minute in-memory cache and a disclosed mock fallback for IMD outages. No forecasts (Phase 3), no agent prompt/wiring changes beyond what the tool needs (Phase 4), no UI.

## Implementation Decisions

### IMD source
- **D-01:** User has no IMD endpoint — the phase researcher must find and recommend the concrete public IMD current-weather source. Planner implements against the researcher's pick.
- **D-02:** Prefer keyless/free public IMD endpoints. `WEATHER_API_KEY` keeps required-semantics (missing key → 502 path) for any source that needs a credential, but Phase 2 must work end-to-end with nothing but the existing `.env` when the chosen source is keyless.
- **D-09 (research fork, user-decided 2026-09-11):** No keyless IMD current-weather API exists (gateway verified 401; scraper 403). Phase 2 ships on **Open-Meteo (keyless, live-verified) as the runtime engine behind the IMD-shaped tool seam** — reply + JSON disclose non-authentic model data. IMD portal registration (JWT + static IP) runs as a parallel human track; IMD-direct cutover deferred to a later phase. `source` field distinguishes engine (`open-meteo`) from fallback (`mock-imd-fallback`).

### Cache policy
- **D-03:** In-memory cache, 10-minute TTL, keyed by normalized location string. No persistent/disk cache in Phase 2.

### Fallback mode
- **D-04:** On IMD outage/timeout, return the existing mock-shaped payload with `"source"` stamped as fallback (e.g. `mock-imd-fallback`) so the agent answers normally — demo never breaks.
- **D-05:** Fallback/cached-stale answers MUST disclose degraded data to the user (reply carries a short staleness/fallback note; JSON carries source + age). Silent fallback is rejected.
- **D-06:** This fallback applies to the IMD data path only. LLM errors keep Phase 1 fail-loudly behavior (honest 502/500, D-06 of Phase 1).

### Location mapping
- **D-07:** Curated in-code map of major Indian cities/districts → whatever the chosen IMD source needs (station code / district id / lat-lon). Normalized (case/whitespace) lookup.
- **D-08:** Unmappable locations → best-guess nearest station AND disclose the guess to the user (no silent substitution, no refusal).

### Claude's Discretion
- Stale-cache serving strategy (stale-while-revalidate vs stale-only-on-error) — planner picks whichever composes cleanly with D-04/D-05; user said "whichever fits well".
- Exact fallback `source` string, cache-age field names, and curated city list size.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts (frozen unless noted)
- `tools/weather.py` — Current mock tool; body gets replaced, name/signature/JSON-string contract stays.
- `services/agent.py` — 30s timeout + 1 retry, threadpool offload (Phase 1); alert parsing consumes tool JSON `alert_level`.
- `api/routes.py` — 502/500 mapping, sanitize + log-full/send-safe (Phase 1, unchanged).
- `core/config.py` — `WEATHER_API_KEY` reserved; required-semantics available.
- `schemas/chat.py` — `ChatRequest`/`ChatResponse` unchanged.
- `main.py` — stdlib logging, X-Request-ID (Phase 1, unchanged).

### Project scope
- `.planning/PROJECT.md` — IMD-direct decision, stack lock.
- `.planning/REQUIREMENTS.md` — DATA-01…DATA-03 definitions.
- `.planning/ROADMAP.md` — Phase 2 goal + 3 success criteria; forecasts (Phase 3) out of scope.
- `.planning/phases/01-backend-hardening/01-CONTEXT.md` — Phase 1 locked decisions (fail-loudly LLM, mock seams, secret redaction).
- `.planning/phases/01-backend-hardening/COVERAGE.md` — "No new external API in Phase 1" declaration; Phase 2 supersedes it for IMD.

## Existing Code Insights

### Reusable Assets
- Mock payload shape in `tools/weather.py` — the exact key set the agent and tests already consume; real data must map into it.
- `get_settings()` + `reset_agent_cache()` — test isolation for key-present/key-missing paths.
- `tests/test_weather_tool.py` — asserts JSON keys + frozen tool name; will need real-source tests with recorded fixtures, not live calls.
- Phase 1 `X-Request-ID` + per-request logging — IMD fetch errors ride the same log path.

### Established Patterns
- Tool returns JSON string; agent parses it — field renames break the agent, so map IMD fields to existing keys.
- Tests patch `api.routes.process_chat`; tool tests call the tool directly — IMD tests must mock HTTP (httpx/responses), never hit live IMD in CI.
- `sanitize_detail` + key redaction (D-17) — IMD error paths must not leak `WEATHER_API_KEY` or endpoint internals.

### Integration Points
- `tools/weather.py` body is the single seam — agent, routes, and schemas are untouched.
- Cache lives inside the tool module (or a small sibling module imported by it) — keyed by normalized location.
- `source` + staleness fields flow through existing JSON into the agent reply and disclosure note.

## Specific Ideas

No specific requirements — user has no IMD endpoint; researcher picks the source.

## Deferred Ideas

None — discussion stayed within phase scope. (Forecasts → Phase 3; location-clarification agent behavior → Phase 4.)

---

*Phase: 2-IMD live data*
*Context gathered: 2026-09-11*
