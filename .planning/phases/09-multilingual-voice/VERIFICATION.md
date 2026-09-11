# Phase 9 (Multilingual Voice) — Verification Report

**Goal (ROADMAP.md):** Chat + voice in Hindi and regional languages via Sarvam
**Requirements:** MULT-01, VOIC-01
**Verified:** 2026-09-11 (UTC), working dir H:/weatherGPT, backend cwd H:/weatherGPT/backend
**Method:** Goal-backward — ran all three gates myself; read implementation, not just summaries.

## Result: PASSED (3/3 success criteria)

| # | Success criterion | Status | Evidence (self-run) |
|---|-------------------|--------|---------------------|
| 1 | Hindi (Devanagari) query → Hindi grounded reply around frozen English core | ✅ VERIFIED | `pytest tests/test_multilingual_chat.py -q` → **9 passed** (self-run). Route test posts Devanagari + `hi-IN`, asserts 200 + `hi-IN` echo + Green + `29.5` byte-identical. `services/multilingual.py:124-129` translates hi→en, calls frozen `process_chat`, derives alert via `_derive_alert_level` on English **before** back-translation. |
| 2 | Voice STT/TTS round-trip mocked in CI | ✅ VERIFIED | `pytest tests/test_multilingual_voice.py -q` → **12 passed** (self-run). Transcribe (WAV upload → transcript + lang echo) and speak (text + hi-IN → `audio/wav` non-empty bytes) both via `httpx.MockTransport` seam; model-routing asserted (`as-IN`→`sarvam-translate:v1`, `hi-IN`→`mayura:v1`); STT `saaras:v3`, TTS `bulbul:v3`/`shubh` pins in `services/sarvam_client.py`. |
| 3 | Graceful degradation + full gates green | ✅ VERIFIED | `pytest tests/ -q` → **117 passed, 2 skipped** (self-run). `xx-YY` → HTTP 200 honest English naming `hi-IN`; as-IN speak → 422 naming as-IN (translated when possible); 3MB → 413 with zero provider calls; forced STT outage → sanitized 502. `pytest tests/test_live_sarvam.py -q -rs` → 1 skipped by default gate. |

## Plus-checks (all hold)

- **Numbers/alerts survive translation:** `29.5` asserted byte-identical in Hindi test (`test_multilingual_chat.py:150`) and per-language rows mr/ta/te/bn/as-IN (`test_multilingual_voice.py:116-125`); `alert_level` derived pre-translation, never translated.
- **English paths unregressed:** `pytest tests/test_chat_api.py tests/test_error_contract.py -q` → **8 passed**; no-language-field path keeps exact `process_chat` call (`api/routes.py:94-98`).
- **Sarvam key never in logs/responses:** `pytest tests/test_multilingual_secrets.py -q` → **6 passed** (forced translate/STT/LLM outages + body + caplog + `sanitize_detail` unit check). Key only on outbound `api-subscription-key` header; `sanitize_detail` redacts all three keys (`routes.py:60-63`); no `print`; `.env.example` carries placeholder only.
- **Agent core untouched:** `git diff HEAD -- backend/services/agent.py` empty; last change to that file is pre-phase refactor `7b62a9d`.
- **No live network in CI except one opt-in skip:** only `tests/test_live_sarvam.py` touches the real path, gated on `RUN_LIVE_SARVAM=1` + key present (module `skipif` + in-test skip); all other Sarvam HTTP via `MockTransport` seam; collect-only confirms exactly one live test.

## Notes

- The 09-02 SUMMARY's "blocked on missing python-multipart" state is **stale/superseded**: voice endpoints landed in commit `c028858`, and the voice suite now collects and passes (multipart present in this env). No action needed.
- Commits observed: `2b3e6d5, 3aa9248, 28bbe3f` (plan 01), `9fa097c, c028858` (plan 02), `3b3112b, 8593076, 8fc0220` (plan 03). Working tree has unrelated uncommitted scaffolding (frontend files, other phase dirs) — none affect Phase 9 verdict.
- Only warnings: two FastAPI `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings in voice tests — cosmetic, non-blocking.

## VERIFICATION PASSED

All 3 success criteria verified with self-run test evidence. No gaps.
