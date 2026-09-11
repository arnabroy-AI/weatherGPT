# Phase 04 Plan 03: Named-Gap Degradation + Secret-Safety Gate — Summary

**Status:** complete
**Date:** 2026-09-11
**Requirements:** AGNT-04

## One-liner

Appended degraded-mode rule 10 to `services/agent.py` SYSTEM_PROMPT (named current-vs-forecast gaps, still-200, LLM 502 path untouched) and proved it with 9 mocked-LLM tests in `tests/test_agent_degraded.py` — full suite 76 passed / 1 pre-existing skip, 85% coverage over the three in-scope modules.

## What was built

### services/agent.py — degraded-mode SYSTEM_PROMPT rule 10 (sole production seam)

- Rule 10 (numbered-imperative style, backticked `process_chat` reference): when tool JSON carries fallback, stale, or forecast-unavailable markers, answer with a still-200 graceful message — name the failed piece (current conditions vs forecast), state what still works (the other data path, cached values, or curated advice), quote usable values exactly, surface the tool note. Never convert tool-data gaps into refusals or 500s; the retry-once-then-fail-loudly path applies to LLM outages only.
- Wording deliberately references "the multi-day forecast tool from rule 2" by number (same technique as Plan 02 rule 8) so Phase 3's pinned invariant `SYSTEM_PROMPT.count("get_weather_forecast") == 1` still holds — verified `forecast-mentions: 1`. Retry loop, threadpool, logging, `_derive_alert_level`, `_TOOLS`, routes, and schemas unchanged.

### tests/test_agent_degraded.py — 9 tests, mocked LLM only (new file)

- `FakeExecutor` patches **only** `services.agent._get_executor`; real tool JSON via `_fallback_payload` and `get_weather_forecast` through an `imd_client` `MockTransport` (current fixture served, daily params raise `ConnectError` to drive the real partial-payload outage branch). Cache-isolation fixture included. Never live network, never OpenRouter.
- Task 1 (degraded, 4 tests): prompt-rules pin (markers, named pieces, still-works, refusal ban, forecast-count invariant); fallback-marked current JSON yields a reply naming current conditions unavailable + what still works + quoted temp/condition; forecast-unavailable partial JSON yields a reply naming forecast unavailable + current values; forced executor exception raises `RuntimeError` with exactly 2 invoke calls (retry-once-then-fail-loudly intact).
- Task 2 (gates, 5 tests): secret-safety test mirroring `tests/test_secrets.py` (sentinel env values + live `get_settings` values + `sk-or`/`sk-test` prefixes asserted absent from `SYSTEM_PROMPT` and `agri_advisories` source); parametrized Alert-regex test over Green/Yellow/Orange/Red × single-day plain and worst-day `(Sat)` paren formats, all resolving via `_derive_alert_level`.

## Verification evidence

- `python -m pytest tests/test_agent_degraded.py tests/test_error_contract.py -q` → **15 passed** (9 new + 6 error-contract, incl. `test_llm_outage_yields_502_with_retry` unregressed)
- `python -m pytest tests/ -q` → **76 passed, 1 skipped** (skip is pre-existing: `test_live_openrouter.py` disabled unless `WEATHERGPT_LIVE=1`; up from 67 passed at Plan 02 with zero regressions)
- Coverage gate (`--cov=services.agent --cov=services.agri_advisories --cov=tools.weather`) → **TOTAL 85%** (agent 87%, agri 94%, weather 83%; misses are pre-existing untested branches — exception-wrap lines, lat/lon parse, guess-note paths — none introduced by this plan)
- `SYSTEM_PROMPT.count("get_weather_forecast") == 1` ✓; rule-10 marker present ✓; stub scan (`TODO|FIXME|placeholder|coming soon|not available`) over the new test file → no hits

## Deviations from Plan

None — plan executed exactly as written. No Rule 1–4 deviations; no threat-surface additions (no new endpoints, auth paths, or schema changes); no stubs; no new runtime deps (T-04-SC — no install step ran).

## Threat flags

None — degraded replies name gaps from sanitized tool markers only, no tracebacks (T-04-05); secret-safety test proves live key values absent from prompt and curated content (T-04-06).

## Git commit

**Best-effort commit did not run (stale lock, as in Plans 01–02):** `git add` blocked by `H:/weatherGPT/.git/index.lock` (`fatal: Unable to create ... File exists`). The lock was left untouched per instructions (never block). Working-tree changes are in place and verified: modified `services/agent.py`, new `tests/test_agent_degraded.py`. Re-run the add/commit once the stale lock is cleared. Note: repo working tree shows everything untracked (`??` on all entries), consistent with prior plans' observations.

## Follow-on

One stray `.coverage.*` data file was created in the repo root by the first coverage attempt (parallel-mode stale-file permission clash); removal was denied by the OS (file locked), so it is left in place — delete it during cleanup. It is not referenced by any code or test. Phase 4 wave 3 is now complete: AGNT-04 delivered, LLM 502 path intact, full suite green.
