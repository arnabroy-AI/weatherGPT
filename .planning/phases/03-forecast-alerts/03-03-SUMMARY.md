# Phase 03 Plan 03: Forecast Cache + Coverage Matrix Summary

**Status:** complete — both tasks done, `tests/test_forecast_cache.py` 6/6 green, full suite 55 passed + 1 skipped (pre-existing skip), zero source changes, zero live network.

## What was built

Hardening + docs-only plan (no `tools/` changes; 03-02 ran concurrently and owns advisories/agent wiring):

- `tests/test_forecast_cache.py` (new, 6 tests, MockTransport only, `_CACHE` isolated around each test):
  - Identical Mumbai 5-day invokes → exactly 1 transport hit; first `cached False`/`cache_age_s 0`, second `cached True`.
  - Mumbai 5-day vs 3-day → 2 hits, proving the days component of the `("forecast", lookup_key, days)` tuple key; 3-day repeat serves cache.
  - `Mumbai` vs `  mumbai  ` → 1 hit, proving normalisation shares one entry.
  - Pre-seeded expired `("forecast", "mumbai", 5)` entry → refetch with 1 hit, `cached False`.
  - Daily `ConnectError` outage → partial: `forecast_days=[]`, `forecast_available False`, note containing `forecast unavailable` + `Mumbai`, live current fields (`temperature_c 26.1`, `feels_like_c 31.8`), `stale False` (variance, see below), `cached False`, elapsed under 5s; healthy retry costs exactly 1 hit, proving no fallback pinning.
  - Secret probe (`WEATHER_API_KEY=SECRET_PROBE_42` + killed daily): probe string in neither returned JSON nor caplog error output (T-03-07).
- `.planning/phases/03-forecast-alerts/COVERAGE.md` (new): decided daily-forecast matrix — INTEGRATE rows for daily fetch, 5-day mapping with per-day alerts, worst-day Alert line, per-day + rollup advisories, location-plus-days 10-min cache, partial fallback, minimal agent wiring; OPT-OUT rows for disk cache (D-06), mock forecast bundles (D-07), stricter thresholds (D-03), orchestration (D-08 → Phase 4).
- `.planning/phases/02-imd-live-data/COVERAGE.md`: Day-wise forecast row flipped from OPT-OUT/Deferred to INTEGRATE with a supersede note pointing at the Phase 3 matrix; all other rows byte-identical.

## Verification evidence

- `python -m pytest tests/test_forecast_cache.py -q` → **6 passed** (3.60s)
- `python -m pytest tests/ -q` → **55 passed, 1 skipped** (7.62s; skip is pre-existing). Plan-01 baseline was 38+1; +6 from this plan, +11 from the concurrently-landed 03-02 `test_forecast_alerts.py` — zero regressions, zero failures.
- Coverage report (`--cov=tools`, `COVERAGE_FILE` redirected to temp because a stale `.coverage.*` lock in the repo root is owned by the concurrent run): **tools/ 82% total** (`imd_client.py` 81%, `weather.py` 83%; misses are lat-lon/guess-note/stale branches covered by other suites' scopes, not this plan's path).
- Direct `--cov` run against the repo root failed with `PermissionError` on a stale `.coverage.<host>.pid*` file — concurrent-run artifact, not a code issue; left untouched.

## Deviations from plan

1. **Partial `stale` flag (minor, actual-contract assertion):** plan task text said the outage partial carries "stale true". The actual Plan 01 contract (`_partial_forecast_payload`) serves fresh live-current values stamped `stale False` via `setdefault` — semantically correct (nothing expired is served). The `stale True` stamp belongs to the expired-entry branch (`_decorate_stale`) and the generic mock fallback. Test asserts the actual contract (`stale is False`) with an explanatory comment; no source change made.
2. **Concurrent 03-02 overlap:** `tests/test_forecast_alerts.py` (11 tests) landed mid-execution; full-suite count went 44 → 55 between runs. No conflicts — separate files, all green together. The `read_first` reference to that file could not be satisfied at task-2 start (it did not exist yet); verification ran against the final combined suite instead.
3. **No `gsd_run`/STATE/ROADMAP updates** per environment notes (explicitly out of scope for this execution).

## Git commits (BEST-EFFORT — blocked, noted per instructions)

No commit was possible: stale `.git/index.lock` persists (same blocker as 03-01 — `fatal: Unable to create 'H:/weatherGPT/.git/index.lock': File exists`), so even `git add` fails. Per environment notes I did not block on this and did not mutate `.git` internals. Files changed (uncommitted, verified present on disk): `tests/test_forecast_cache.py` (new), `.planning/phases/03-forecast-alerts/COVERAGE.md` (new), `.planning/phases/02-imd-live-data/COVERAGE.md` (one-row flip).

## Known stubs / threat flags

None. No `TODO`/placeholder/empty-value stubs; no new endpoints, auth paths, or dependencies (T-03-SC: no new packages). T-03-06 (no-pinning) proven by the outage-retry hit count; T-03-07 (redaction) proven by the secret-probe test.

## DoD mapping

- Identical queries hit cache within TTL with day-count key isolation: ✅ (1-hit / 2-hit / normalisation / expiry tests)
- Outage → partial current-only + honest note, sub-5s: ✅ (partial shape + timing + no-pinning)
- Secrets never leak: ✅ (probe absent from JSON and logs)
- Matrices decide daily forecast INTEGRATE: ✅ (Phase 3 matrix + Phase 2 row flip)
- Full suite passes: ✅ (55 passed, 1 pre-existing skip)

## Self-Check: PASSED

- `tests/test_forecast_cache.py`, both COVERAGE.md files present on disk with the specified content; `git status` shows them as untracked/modified (commit blocked only by the stale lock).
- No commits to verify (documented above, not a code gap).
