# Phase 10: Proactive push alerts - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

FCM push dispatch + hourly threshold watcher over the 18 mapped cities with 6h dedup. Service-account auth, key-free logs, mocked FCM in CI. No SMS/WhatsApp (needs keys), no frontend subscription UI (endpoints only), English + language-prefed alert copy where trivially reusable.

## Implementation Decisions

### Watcher
- **D-01:** Watch all 18 mapped cities, hourly evaluation, dispatch on Orange + Red only. Green/Yellow never push.

### Targeting
- **D-02:** Send endpoint (direct token + topic paths) PLUS subscribe endpoints for token/topic registration. In-memory registry (no DB in v1).

### Dedup
- **D-03:** One dispatch per location+level per 6 hours; severity upgrades (Orange→Red) re-fire immediately.

### Claude's Discretion
- FCM library choice (firebase-admin vs raw httpx to FCM v1 — prefer fewer deps), payload shape, registry structure, watcher trigger (scheduler vs manual+cron endpoint).

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- FCM credential: `backend/fcm-service-account.json` (shape VALIDATED 2026-09-11; project weathergpt-4014b). Load path via `FCM_SERVICE_ACCOUNT_FILE` setting; missing file → clear startup/test skip, never crash import.
- `tools/imd_client.py` `derive_alert_level` — the threshold authority; watcher reuses it, never a second heuristic.
- `tools/weather.py` city map + cache — watcher reads through the same cached seam (no extra provider load).
- `api/routes.py` error mapping + throttle + sanitize; `core/config.py` settings pattern.
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (NOTF-01, NOTF-02), `.planning/ROADMAP.md` (Phase 10 criteria).

## Existing Code Insights

### Reusable Assets
- Phase 9 route additions (voice endpoints) — same router, same throttle/sanitize patterns for new endpoints.
- MockTransport test philosophy — FCM HTTP mocked; service-account file faked in tests, never the real key.
- `get_settings()` + `cache_clear()` test isolation.

### Established Patterns
- Secrets never in code/logs/responses; sentinel tests mandatory.
- `attrib -R` before editing R-flagged files; backend cwd for pytest.

### Integration Points
- New `services/fcm_client.py` (auth + send) + `services/alert_watcher.py` (evaluate + dedup + registry) + routes (`/alerts/subscribe`, `/alerts/dispatch` or planner's naming).
- Watcher trigger: planner picks (in-process scheduler vs callable + docs). No new runtime deps preferred.

## Specific Ideas

No specific requirements — standard FCM v1 patterns.

## Deferred Ideas

- SMS/WhatsApp dispatch (needs keys + DLT). Frontend push-subscribe UI. Persistent registry (DB) → v2.

---

*Phase: 10-Proactive push alerts*
*Context gathered: 2026-09-11*
