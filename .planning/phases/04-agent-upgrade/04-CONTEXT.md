# Phase 4: Agent upgrade - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Upgrade the agent's conversational behavior: enforced tool-grounding, one-follow-up location flow, curated + live agri/climate answers, and graceful named-gap degradation. No new data tools, no schema/route changes, no UI.

## Implementation Decisions

### Grounding enforcement
- **D-01:** Strengthen SYSTEM_PROMPT grounding rules AND add mocked-LLM tests proving reply values match tool JSON (temperatures, alerts). Prompt-only trust rejected.
- **D-02:** Rewrite stale prompt rule 6 to mandate disclosure wording: cite non-IMD model data + surface fallback/stale notes in replies.

### Location flow
- **D-03:** Exactly ONE clarifying follow-up when location is unknown/unmappable, then a best-effort answer. No persisting, no refusal.
- **D-04:** No default city. Never assume Delhi or anywhere silently.

### Agri + climate
- **D-05:** Curated static advisories (crop × season cues, in code or prompt-adjacent data) COMBINED with live tool weather grounding.
- **D-06:** Open-ended v1 scope: any agri/climate question answered best-effort from curated base + live data — not restricted to a crop list.

### Degraded chat
- **D-07:** Tool outage mid-chat → still-200 graceful message ("data unavailable, here's what I know"), NOT an honest 502. (LLM-outage fail-loudly from Phase 1 unchanged — this is the tool-data path.)
- **D-08:** Degraded messages NAME the failed piece (current vs forecast) + state what still works. Generic error text rejected.

### Claude's Discretion
- Exact prompt wording, curated advisory content/size, mocked-LLM test harness shape.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- `services/agent.py` — SYSTEM_PROMPT (rules 1-7, rule 6 stale), `_TOOLS`, retry loop, `_derive_alert_level`, `process_chat`.
- `tools/weather.py` — both tools, cache, fallback JSON, city map, disclosure fields.
- `tools/imd_client.py` — `derive_alert_level`, advisories, rollup, alert_line format.
- `api/routes.py`, `schemas/chat.py`, `main.py`, `core/config.py` — unchanged in Phase 4.

### Project scope
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (AGNT-01…AGNT-04), `.planning/ROADMAP.md` (Phase 4 goal + criteria).
- `.planning/phases/03-forecast-alerts/03-CONTEXT.md`, `.planning/phases/02-imd-live-data/02-CONTEXT.md` — carry over.

## Existing Code Insights

### Reusable Assets
- Mocked seams: tests patch `api.routes.process_chat`; tool tests call tools directly. Agent-behavior tests need a MOCKED LLM (fake ChatOpenAI/AgentExecutor output) — new harness, same philosophy.
- `intermediate_steps` tool-JSON recovery in `process_chat` — grounding tests can assert on it.
- `_derive_alert_level` triple fallback (Alert: line → tool JSON → keywords) — keep; prompt changes must keep emitting the line.

### Established Patterns
- Prompt rules are numbered imperatives; tool mentions use backticked names. Follow the same style.
- Disclosure strings live in tool JSON (`source`, advisory qualifiers) — prompt rule 6 rewrite must reference them, not duplicate.
- Log-full/send-safe, key redaction — prompt/curated content must contain no secrets.

### Integration Points
- SYSTEM_PROMPT is the single seam; `_TOOLS` list unchanged (no new tools).
- Curated agri data: new module or prompt-adjacent constant imported by agent — planner picks; must be test-assertable.
- Reply path (`reply` + `alert_level`) unchanged — graceful degradation composes with existing fallback JSON.

## Specific Ideas

No specific requirements — open to standard approaches.

## Deferred Ideas

None — multi-turn memory beyond one follow-up not requested; voice/multilingual stay v2.

---

*Phase: 4-Agent upgrade*
*Context gathered: 2026-09-11*
