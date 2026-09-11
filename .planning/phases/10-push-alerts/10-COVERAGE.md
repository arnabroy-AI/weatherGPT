# Phase 10: Proactive push alerts — API coverage matrix

**Phase:** 10-push-alerts · **Date:** 2026-09-12
**Engine:** FCM v1 (`https://fcm.googleapis.com/v1/projects/{project_id}/messages:send`)
via raw `httpx` behind the token-provider seam, wrapped around the frozen
cached tool seam (`get_current_weather` over all 18 mapped cities, Orange +
Red only, 6h dedup).
CI posture: `httpx.MockTransport` plus mocked bearer only, with one tiny opt-in
live validate_only test maximum (`tests/test_live_fcm.py`, skipped by default).

## INTEGRATE

| Capability | Status | Requirement | Scope note |
|------------|--------|-------------|------------|
| Direct-token send via FCM v1 `messages:send` behind the token-provider seam | INTEGRATE | NOTF-01 | `POST /api/alerts/send` with `token` + Orange/Red title/body; Bearer header via injected provider in CI, lazy `google-auth` opt-in live; `POST /api/alerts/subscribe` registers tokens in-memory; MockTransport-only in CI. |
| Topic send to `alerts-<slug>` via FCM v1 `messages:send` behind the token-provider seam | INTEGRATE | NOTF-01 | `POST /api/alerts/send` with `topic` plus hourly fan-out from `POST /api/alerts/check` to `alerts-<slug>` and subscribed tokens; title `WeatherGPT <level> alert for <location>`, body advisory truncated to 200 chars; MockTransport-only in CI. |
| Threshold evaluation over all 18 cities through the cached seam with `derive_alert_level` as sole authority | INTEGRATE | NOTF-02 | `services/alert_watcher.py` `evaluate_city` reads `get_current_weather` JSON (`alert_level`/`advisory`/`location` straight from the payload, no second heuristic); `GET /api/alerts/status` reports 18 cities + 6h cooldown + counts; MockTransport-only in CI. |

## OPT-OUT

| Capability | Status | Requirement | Reason |
|------------|--------|-------------|--------|
| SMS / WhatsApp dispatch | OPT-OUT | NOTF-01 | Provider key plus DLT registration absent; deferred per 10-CONTEXT — FCM push only in v1, no SMS/WhatsApp credentials wired. |

## Notes

- Cooldown: one dispatch per location+level per 6 hours (`COOLDOWN_S=21600`); severity upgrades (Orange→Red) re-fire immediately, downgrades stay silent inside the window.
- `google-auth` stays a lazy opt-in for live sends (`pip install google-auth`); zero new runtime deps — `backend/requirements.txt` stays byte-identical (T-10-SC).
- Live posture: single `validate_only` benign Orange topic payload (`tests/test_live_fcm.py`, skipped unless `RUN_LIVE_FCM=1`) so nothing delivers.
- Key posture: service-account JSON loads per call via `FCM_SERVICE_ACCOUNT_FILE` (missing file disables cleanly); private key, access token, and device tokens travel only on the outbound FCM header/payload, never in logs or response bodies — sentinel suite in `tests/test_fcm_secrets.py`; subscribe/status echo at most the token last-6 plus counts.
