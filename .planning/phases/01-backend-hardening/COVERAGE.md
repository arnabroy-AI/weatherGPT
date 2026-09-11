# Phase 1 Coverage Declaration (D-02 pass-plus-report gate)

**Declaration:** Phase 1 hardens the existing FastAPI baseline against the
**mock** weather tool only. It integrates **no new external service and no new
external API**, so no API coverage matrix applies to this phase.

- The pre-existing OpenRouter integration (`services/agent.py` via
  `ChatOpenAI`) is **untouched** — no new endpoints, models, or credentials.
  The only live-network test (`tests/test_live_openrouter.py`) is opt-in and
  skipped by default (`WEATHERGPT_LIVE=1` required), so CI stays deterministic.
- Real IMD integration arrives in **Phase 2**; that phase will own the
  external-API matrix (endpoints, auth, timeouts, fixtures).

**Gate (D-02):** `python -m pytest tests/ -q --cov=. --cov-report=term-missing`
must exit 0 (all tests pass) with the coverage report rendered. There is no
hard coverage threshold in Phase 1 — pass plus report.
