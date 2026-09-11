# Phase 04 Plan 01: Tracer Grounded-Reply Slice — Summary

**Status:** complete
**Date:** 2026-09-11
**Requirements:** AGNT-01, AGNT-02

## One-liner

Upgraded `services/agent.py` SYSTEM_PROMPT with grounding/disclosure/one-follow-up rules (D-01..D-04) and proved the slice with a mocked-LLM harness in `tests/test_agent_grounding.py` (5 tests green, full suite 60 passed / 1 pre-existing skip).

## What was built

### services/agent.py — upgraded SYSTEM_PROMPT (rules 1–7, sole production seam)

Kept the numbered-imperative style, backticked tool names, `_TOOLS` list, 30 s retry/threadpool/logging, `process_chat` signature, and `_derive_alert_level` regex untouched. Changes per locked decisions:

1. **D-01 grounding:** Rule 1 mandates calling `` `get_current_weather` `` and quoting `temperature_c` / `condition` / `alert_level` exactly as returned in the tool JSON; new rule 2 does the same for `` `get_weather_forecast` `` per-day values. "Never invent observations" retained in both.
2. **D-02 disclosure:** Rule 6 rewritten to mandate disclosure wording — state figures are **non-IMD model data**, repeat the tool `source` note, and surface any fallback/stale notes from the tool JSON in the reply.
3. **D-03 one follow-up:** Rule 5 encodes exactly ONE clarifying follow-up when the location is unknown/unmappable, then a best-effort answer — never a refusal.
4. **D-04 no default city:** Rule 5 forbids assuming a default city such as Delhi.
5. **Alert carryover:** Rule 4 (`Alert: <Green|Yellow|Orange|Red>` on its own line) kept verbatim-compatible, so worst-day lines like `Alert: Orange (Sat)` still match the Phase 1 reply regex.

### tests/test_agent_grounding.py — mocked-LLM harness + 5 tests (new file)

- `FakeExecutor` patches **only** `services.agent._get_executor`; `invoke` returns canned output plus `intermediate_steps` carrying REAL tool JSON obtained by calling `get_current_weather` through `imd_client` `MockTransport` serving `tests/fixtures/open_meteo_mumbai.json` (never live network, never OpenRouter).
- Tracer tests: reply quotes tool `temperature_c` + `condition`; reply contains `non-IMD model data`; reply Alert line matches `Alert:\s*(Green|Yellow|Orange|Red)` and `alert_level` equals the tool value.
- Location tests (D-03/D-04): unknown location with no context yields exactly one clarifying question (`?` count == 1, no `°C` values, no tool call); follow-up carrying a location yields a grounded disclosed reply. No default-city assertion anywhere in the file (no `Delhi` string).

## Verification evidence

- `python -m pytest tests/test_agent_grounding.py -q` → **5 passed**
- `python -m pytest tests/ -q` → **60 passed, 1 skipped** (skip is pre-existing: `test_live_openrouter.py` disabled unless `WEATHERGPT_LIVE=1`)
- `Select-String "Alert:" services/agent.py` → matches rule line 42 + `_derive_alert_level` (regex intact)
- `Select-String "non-IMD model data" services/agent.py` → rule 6 ✓
- `Select-String "ONE clarifying|Delhi" services/agent.py` → rule 5 ✓
- Only patch target in test file is `services.agent._get_executor` ✓

## Deviations from Plan

None — plan executed exactly as written. No Rule 1–4 deviations; no threat-surface additions (no new endpoints, auth paths, or schema changes); no stubs.

## Git commit

**Best-effort commit FAILED (stale lock, as anticipated):** `git add` + `git commit` blocked by `H:/weatherGPT/.git/index.lock` (`fatal: Unable to create ... File exists`). The lock was left untouched per instructions (never block). Working-tree changes are in place and verified: modified `services/agent.py`, new `tests/test_agent_grounding.py`. Re-run the commit once the stale lock is cleared.

## Follow-on

Plan 02 (agri advisories) and Plan 03 (degraded-mode rules + secret-safety gate) build on the `SYSTEM_PROMPT` seam and `FakeExecutor` harness established here. The LLM-outage fail-loudly 502 pattern in `tests/test_error_contract.py` was left untouched.
