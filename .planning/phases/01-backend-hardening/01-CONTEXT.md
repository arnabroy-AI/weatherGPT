# Phase 1: Backend hardening - Context

**Gathered:** 2026-09-10
**Status:** Ready for planning

## Phase Boundary

Harden the existing FastAPI + LangChain scaffold into a production-ready, tested baseline: `POST /api/chat` + `GET /health` with clear error contracts, logging, request tracing, and pytest coverage — all against the **mock** weather tool. No real IMD integration (Phase 2), no forecasts (Phase 3), no agent upgrades (Phase 4).

## Implementation Decisions

### Test strategy
- **D-01:** Mock at `services.agent.process_chat` for route/schema tests — fastest, keeps LLM out of the suite.
- **D-02:** Gate is "pytest must pass + coverage reported", no hard coverage gate in Phase 1.
- **D-03:** Flat layout: `tests/test_chat_api.py` + `tests/test_weather_tool.py` (+ `tests/conftest.py` as needed).
- **D-04:** Fully mocked by default; one opt-in live OpenRouter test, skipped unless explicitly enabled (env flag), so CI stays deterministic.

### Error contract
- **D-05:** Keep current mapping: missing key / LLM failure → 502 with friendly detail; unexpected → generic 500. No new 504 in Phase 1.
- **D-06:** Fail loudly on LLM outage (honest 502/500), no degraded-200 masking — visibility over demo smoothness in Phase 1.
- **D-07:** Log full traceback server-side; client receives only safe `detail` strings, never internals.

### Observability
- **D-08:** Stdlib `logging`, human-readable lines, INFO default. No JSON structured logs yet.
- **D-09:** Add `X-Request-ID` middleware: echo incoming header, generate UUID when absent, include it in logs and error responses.
- **D-10:** `/health` stays liveness-only (`{status, app, version}`). No dependency checks in Phase 1.

### Hardening limits
- **D-11:** LLM call timeout 30s with 1 retry, then 502. Applied in the agent layer.
- **D-12:** CORS stays `allow_origins=["*"]` for local dev; tightening moves to Phase 7 behind an env var.
- **D-13:** Fix sync-in-async blocking now: run sync `process_chat` in a threadpool (`anyio.to_thread` / `run_in_threadpool`) so `/chat` never blocks the event loop.
- Rate limiting explicitly deferred to Phase 7 (recorded under Discretion as informational — no work in this phase).

### Input validation
- **D-15:** Keep schema limits as-is (`message` 1–2000 chars, `location` ≤120, strip whitespace). No extra prompt-injection defenses in Phase 1.

### Pytest setup
- **D-16:** `pytest` + `httpx` ASGI transport + `pytest-asyncio` (`asyncio_mode=auto`) for async route tests.

### Secret safety
- **D-17:** Never log API keys; redact in error paths; add a test asserting key material never appears in logs/responses.

### Claude's Discretion
- **D-14 [informational — no work in this phase]:** No rate limiting in Phase 1; throttling (slowapi or equivalent) deferred to Phase 7 with the frontend. Deliberate deferral, nothing to build or verify now.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### API + agent contracts
- `api/routes.py` — Current `/chat` route, error mapping (502/500), response model wiring.
- `services/agent.py` — AgentExecutor construction, `process_chat(message, location)` signature, `Alert:` parsing + heuristic fallback.
- `schemas/chat.py` — `ChatRequest` (message/location limits) and `ChatResponse` (reply/alert_level) contracts.
- `core/config.py` — `BaseSettings` loading, `OPENROUTER_API_KEY` validation, model/base-url defaults.
- `tools/weather.py` — Mock `get_current_weather(location) -> JSON string` contract (do not change signature in Phase 1).
- `main.py` — FastAPI app, permissive CORS, `/health` liveness shape.

### Project scope
- `.planning/PROJECT.md` — Stack lock, out-of-scope list (no auth, English-only v1).
- `.planning/REQUIREMENTS.md` — BACK-01…BACK-04 definitions.
- `.planning/ROADMAP.md` — Phase 1 goal + 4 success criteria; Phase 2+ boundaries (IMD, forecasts) are out of scope here.

## Existing Code Insights

### Reusable Assets
- `AgentExecutor` + `create_tool_calling_agent` wiring in `services/agent.py`: keep, only add timeout/retry + threadpool offload at call site.
- `_derive_alert_level()` heuristic: keep as-is; covered by tool-contract test.
- `get_settings()` lru_cache + `reset_agent_cache()`: reuse in tests to isolate env changes.

### Established Patterns
- Routers are traffic directors (`api/routes.py`): no business logic migrates into routes.
- Tool returns JSON string: tests assert parseable JSON with `location`, `temperature_c`, `alert_level` keys.
- `BaseSettings` + `.env`: tests set dummy keys via monkeypatch, never real secrets.

### Integration Points
- `POST /api/chat` is the single seam the frontend (Phase 6) will call — response shape `{reply, alert_level}` is frozen in Phase 1.
- `X-Request-ID` middleware slots into `main.py` alongside existing CORSMiddleware.
- Logging configuration belongs at app startup in `main.py`, request-id bound per request.

## Specific Ideas

No specific requirements — open to standard approaches (stdlib logging, pytest-asyncio auto, httpx ASGI transport).

## Deferred Ideas

None — discussion stayed within phase scope. (Rate limiting and CORS tightening explicitly deferred to Phase 7; IMD work stays in Phase 2.)

---

*Phase: 1-Backend hardening*
*Context gathered: 2026-09-10*
