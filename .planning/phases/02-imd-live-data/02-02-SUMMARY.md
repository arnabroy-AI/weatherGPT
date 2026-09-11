# Phase 02 Plan 02: 10-min TTL cache + outage fallback — Summary

**Phase:** 02-imd-live-data · **Plan:** 02 · **Type:** execute · **Date:** 2026-09-11
**Status:** complete (code + tests green; git commit blocked by stale lock — see § Commits)
**Requirements:** DATA-02

## One-liner

Repeated `get_current_weather` queries within 10 minutes cost exactly one
upstream call (lock-guarded TTL cache keyed by normalised location), and a
dead provider still returns stamped, disclosed fallback JSON in well under 5
seconds — stale-expired entry when one exists, else the mock-shaped
`mock-imd-fallback` payload.

## What was built

- **`tools/weather.py`** (body only; tool name/signature/14 frozen keys untouched)
  - `CACHE_TTL_S = 600`, module-level `_CACHE` dict, `_CACHE_LOCK =
    threading.Lock()` (D-03, T-02-04; safe under the Phase 1 threadpool offload).
  - Key = `location.strip().lower()`; entry = `{expires, stored_at
    (monotonic), payload}`. Fresh fetch stores the base 14-key payload;
    disclosure stamps (`cached`, `cache_age_s`, `stale`) are applied per
    return, never stored.
  - Fresh → `cached false`, `cache_age_s 0`, `stale false`. Within-TTL hit →
    `cached true`, `cache_age_s` = int seconds since store, `stale false`.
  - Outage branch (`except Exception`, covering `httpx.HTTPError`/timeouts
    and `ValueError`/`KeyError`/`TypeError`/`RuntimeError` from schema
    mismatch): stale-only-on-error — expired entry served with `stale true`,
    `cache_age_s`, source suffixed `+stale-fallback`; otherwise generic
    fallback with `source` exactly `mock-imd-fallback`, `temperature_c 29.5`,
    `condition "Light rain unavailable"`, `alert_level Yellow`, `stale true`,
    `cached false`. Both branches append the literal `Note: live data
    unavailable; showing fallback values.` to `advisory` (D-04/D-05).
    Full traceback to server log only; user JSON never carries keys, URLs,
    or tracebacks (T-02-05). Fallbacks are never stored as fresh (T-02-04).
  - Untouched: `tools/imd_client.py`, `services/agent.py`, `api/routes.py`,
    schemas, `main.py`, `core/config.py`; LLM fail-loud path unchanged (D-06).
- **`tests/test_imd_client.py`** — 4 new tests + autouse `_isolate_weather_cache`
  fixture (clears the TTL dict around every test so transport-hit counts are
  order-independent):
  - `test_cache_hit` — two identical Pune invokes, exactly 1 transport hit;
    first `cached false`/`cache_age_s 0`, second `cached true`/non-negative int.
  - `test_ttl_expiry` — pre-seeded expired Pune entry refetches (1 hit,
    `cached false`, live source).
  - `test_outage_fallback` — `httpx.ConnectError` transport → parseable JSON,
    source exactly `mock-imd-fallback`, all 14 keys, advisory contains `live
    data unavailable`, deterministic placeholders, wall time < 5 s; plus
    follow-up healthy invoke refetches (fallback never pinned the cache).
  - `test_stale_on_error` — expired Pune entry + dead transport → `stale
    true`, source ends `+stale-fallback`, disclosure present,
    `temperature_c 26.1` proving the expired entry (not the generic 29.5
    mock) was served.

## Deviations from Plan

None — plan executed exactly as written. Two conforming adjustments worth noting
(not deviations, both inside plan discretion):

1. **Fallback `source` tightened to the exact literal `mock-imd-fallback`.**
   Plan 01's interim fallback carried a longer parenthetical source string;
   this plan's acceptance criterion requires the exact literal, so the string
   was shortened. Disclosure is preserved via `advisory` + `stale`/`cached` fields.
2. **Cache-isolation fixture added to the test file.** Required for the
   hit-count assertions to hold regardless of test order (Plan 01 tests cache
   Mumbai/Pune entries otherwise). No existing test was modified.

No new packages (stdlib `threading`/`time` only) — no legitimacy gate triggered.

## Verification evidence

- `python -m pytest tests/test_imd_client.py tests/test_weather_tool.py -q`
  → **10 passed**
- `python -m pytest tests/ -q` → **26 passed, 1 skipped** (skip = opt-in live
  OpenRouter test, `WEATHERGPT_LIVE` unset — expected; suite was 22 passed +
  1 skipped before this plan, +4 new tests = 26, no regressions)
- Threat check: T-02-04 (normalised key, lock-guarded, fallbacks never stored
  as fresh — proven by the post-fallback refetch assertion), T-02-05
  (log-full/send-safe; user payload carries source + age only), T-02-06
  (outage path measured < 5 s in-test; 6.0 s httpx timeout unchanged).

## Known stubs / deferred

- None in this slice. Curated city map stays minimal (Mumbai + Pune);
  full city-map coverage belongs to its own plan.

## Commits

- **Blocked, best-effort attempted:** `git add tools/weather.py
  tests/test_imd_client.py` + `git commit` fails with `fatal: Unable to
  create 'H:/weatherGPT/.git/index.lock': File exists` (stale lock, same as
  Plan 01; repo still has no commits on `main`). Both files are complete on
  disk and verified by the pytest runs above; commit when the lock clears.

## Self-Check

- [x] `CACHE_TTL_S == 600` and `_CACHE_LOCK` is a `threading.Lock` (asserted in test)
- [x] Two identical invokes → 1 transport hit, second `cached true`
- [x] Expired entry → refetch with `cached false`
- [x] Outage → `mock-imd-fallback` source, 14 keys, disclosure, < 5 s
- [x] Stale-entry outage → `stale true`, `+stale-fallback` source, fixture values
- [x] Full suite green with no regressions (26 passed, 1 expected skip)
- [ ] Commits exist — **FAILED (environment)**, documented above; no code impact
