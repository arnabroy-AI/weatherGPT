# Phase 04 Plan 02: Curated Agri Advisories + Live Grounding — Summary

**Status:** complete
**Date:** 2026-09-11
**Requirements:** AGNT-03

## One-liner

New dependency-free `services/agri_advisories.py` curated base (6 crops × season cues + best-effort fallback, every entry non-IMD qualified) combined with live tool values via two new SYSTEM_PROMPT agri rules in `services/agent.py`, proved by 7 mocked-LLM tests in `tests/test_agent_agri.py` (full suite 67 passed / 1 pre-existing skip).

## What was built

### services/agri_advisories.py — curated advisory base (new file)

- Dependency-free module (stdlib `re` only): `get_advisory(crop="", season="")` plus a `lookup_advisory` alias, matching case-/whitespace-insensitively over the combined crop/season text.
- Covers paddy, wheat, cotton, sugarcane, maize, soybean with kharif/rabi/summer defaults; `monsoon→kharif`, `winter→rabi`, `zaid→summer` cue aliases (so `get_advisory("PADDY sowing", "Monsoon")` hits the paddy-kharif note).
- Unknown/empty crops yield the generic best-effort fallback per D-06 (never a refusal); every returned string is guaranteed to carry the non-IMD qualifier (stored texts mirror the `tools/imd_client.py` `_build_advisory` wording authority, with a function-level backstop append).
- No secrets, no user data, no network, no tool registration — prompt-adjacent data per D-05, not a replacement for tool calls. `_TOOLS` untouched (still exactly two entries).

### services/agent.py — agri/climate SYSTEM_PROMPT rules 8–9 (sole production seam)

- Rule 8: for agri/climate questions call `` `get_current_weather` `` and, for sowing/harvest timing, the multi-day forecast tool from rule 2, then combine live values with the curated advisory base, quoting live `temperature_c`/per-day values exactly — never invent observations.
- Rule 9: answer any crop best-effort (generic fallback for unknown crops, still live-grounded); rules 4 (Alert line) and 6 (non-IMD disclosure) apply to agri replies.
- Numbered-imperative style kept; retry loop, threadpool, logging, `_derive_alert_level`, routes, and schemas unchanged.

### tests/test_agent_agri.py — mocked-LLM harness + 7 tests (new file)

- Reuses the Plan 01 `FakeExecutor` pattern (patches only `services.agent._get_executor`); real tool JSON via a routing `MockTransport` serving the recorded current + forecast fixtures (never live, never OpenRouter); cache-isolation fixture included.
- Curated tests (`-k curated` selects 5): paddy/kharif non-empty + non-IMD; case/whitespace + monsoon→kharif equivalence; unknown-crop fallback best-effort with no refusal phrasing.
- Grounding tests: Nashik paddy reply contains the curated transplant note AND the live `temperature_c` with Alert line matching `alert_level`; unknown-crop (dragonfruit/Pune) reply contains the generic fallback + live temp with no refusal; climate summary grounds in forecast JSON day date + `temp_max_c` + `alert_line`; prompt-rules test pins both tools, the curated base, best-effort, the Phase 3 single-mention invariant, and `_TOOLS == 2`.

## Verification evidence

- `python -m pytest tests/test_agent_agri.py -q -k curated` → **5 passed, 2 deselected**
- `python -m pytest tests/test_agent_agri.py -q` → **7 passed**
- `python -m pytest tests/test_agent_grounding.py -q` → **5 passed** (no regression)
- `python -m pytest tests/ -q` → **67 passed, 1 skipped** (skip is pre-existing: `test_live_openrouter.py` disabled unless `WEATHERGPT_LIVE=1`)
- `Select-String "curated|forecast tool from rule 2|best-effort" services/agent.py` → rules 8–9 ✓
- `Select-String "_TOOLS = " services/agent.py` → `[get_current_weather, get_weather_forecast]` ✓

## Deviations from Plan

**1. [Rule 3 — Blocking] Agri rule 8 references the forecast tool via rule 2 instead of a second literal mention.**
- **Found during:** Task 2 — full-suite run failed `tests/test_forecast_alerts.py::test_agent_prompt_single_forecast_rule` (`SYSTEM_PROMPT.count("get_weather_forecast") == 1`), a Phase 3 pin on the single canonical forecast rule.
- **Fix:** Rule 8 directs "the multi-day forecast tool from rule 2" for sowing/harvest timing rather than repeating the literal name; the tool call is still mandated, and the prompt-rules test pins the `forecast tool from rule 2` phrase plus the count invariant. No other file touched (per touch-scope constraint); `_TOOLS`, rule 2, and all Phase 3 behavior unchanged.
- **Files modified:** `services/agent.py`, `tests/test_agent_agri.py` (both in-plan files).

No Rule 1/2/4 deviations; no threat-surface additions (no new endpoints, auth paths, or schema changes); no stubs; no new runtime deps (T-04-SC — no install step ran).

## Threat flags

None — curated static agronomy text only (T-04-03: no secrets/user data/network); prompt rules reference curated base + live tools with values pinned to tool JSON by tests (T-04-04).

## Git commit

**Best-effort commit did not run (stale lock, as in Plan 01):** `git add` blocked by `H:/weatherGPT/.git/index.lock` (`fatal: Unable to create ... File exists`). The lock was left untouched per instructions (never block). Working-tree changes are in place and verified: new `services/agri_advisories.py`, modified `services/agent.py`, new `tests/test_agent_agri.py`. Re-run the add/commit once the stale lock is cleared.

## Follow-on

Plan 03 (degraded-mode rules + secret-safety gate) builds on the SYSTEM_PROMPT seam and the `FakeExecutor` harness. The agri fallback composes with existing tool-outage fallback JSON (rules 6/9 surface stale notes in agri replies too).
