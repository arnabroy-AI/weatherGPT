# Phase 09 Plan 01: Hindi Round-Trip Tracer — Summary

**Status:** complete
**Date:** 2026-09-11
**Requirements:** MULT-01
**Commits:** 2b3e6d5, 3aa9248, 28bbe3f

## One-liner

Hindi chat round-trip via Sarvam Mayura translate wrapped around the frozen English agent core, with digits and alert level preserved and English clients unaffected.

## Objective achieved

Proved the production-quality Hindi round-trip tracer end-to-end per D-01, D-03, D-04: Devanagari query → English via mocked Sarvam translate → frozen English agent core → back to Hindi, with `29.5` and `alert_level: Green` surviving byte-identical. Agent core (`services/agent.py`) untouched — verified via `git diff --stat` (no output).

## Tasks completed

### Task 1 — End-to-end Hindi round-trip (tracer) — `2b3e6d5`

- `backend/services/sarvam_client.py` (new): synchronous httpx translate client pinned to `mayura:v1` (model pin per Claude's Discretion, noted in commit body), `numerals_format: international`, 15 s timeout, header `api-subscription-key`, 1000-char sentence-boundary chunking with a byte-identical fast path for short inputs, module-level transport seam mirroring `imd_client.set_transport`, sanitized `RuntimeError` (never carries the key), server-side `logger.exception`.
- `backend/services/multilingual.py` (new): `process_multilingual_chat(message, location, language)` — hi-IN round-trip with `_derive_alert_level` on the English reply **before** back-translation; `SUPPORTED_LANGUAGES` six-code set; `normalize_language`/`canonical_language` helpers; en-IN short-circuit to frozen `process_chat`.
- `backend/tests/test_multilingual_chat.py` (new, 6 tests): MockTransport translate-shape assertions, missing-key/non-200 sanitized errors, chunking fan-out, direct orchestration digit preservation (`29.5`), English passthrough.

### Task 2 — Schema language field + route wiring — `3aa9248`

- Cleared Windows read-only flags on `schemas/chat.py` and `api/routes.py` via `attrib -R` before editing.
- `ChatRequest.language`: optional, default `en-IN`, `max_length 10`. `ChatResponse.language`: echo field, default `en-IN`.
- Route normalizes (strip + lowercase), keeps the exact `process_chat` path for en-IN/absent, delegates otherwise to `process_multilingual_chat`; unknown codes get HTTP 200 honest English reply naming all six codes + en-IN, never reaching the provider (T-09-01).
- `sanitize_detail` now also redacts `SARVAM_API_KEY` (T-09-03). Throttle, `run_in_threadpool`, 422/502/500 mapping unchanged.

### Task 3 — Route-level tests — `28bbe3f`

- Three ASGI route tests: hi-IN round-trip (real orchestration + mocked translate + mocked executor → 200, `hi-IN`, Green, `29.5` intact), no-language English default (reply untouched, `en-IN`), `xx-YY` honest fallback (200, `en-IN`, names `hi-IN`).

## Verification evidence

- `pytest tests/test_multilingual_chat.py -q` → 9 passed.
- `pytest tests/test_multilingual_chat.py tests/test_chat_api.py tests/test_error_contract.py -q` → 14 passed.
- Full suite `pytest tests/ -q` → **99 passed, 1 skipped** (pre-plan baseline: 90 passed, 1 skipped; +9 new, zero regressions).
- No live network: all Sarvam HTTP via `MockTransport` (module seam or per-call `transport`); the only `.env` key touched is a monkeypatched sentinel; `SARVAM_API_KEY` never logged/printed.

## Deviations

None — plan executed exactly as written, except one internal auto-fix during Task 1: the first chunking implementation whitespace-normalized short replies (`\n` → space), breaking the byte-identical back-translation input assertion. Fixed with a fast path returning sub-1000-char inputs untouched ([Rule 1 — Bug], same commit `2b3e6d5`).

## Threat model coverage

- T-09-01: normalize + allowlist + honest fallback — implemented in route + `multilingual.canonical_language`.
- T-09-02: `numerals_format: international` + pre-translation alert derivation — implemented, asserted (`29.5`, `alert_level`).
- T-09-03: log-full/send-safe + `sanitize_detail` redaction — implemented.
- T-09-04: 1000-char chunking; schema 2000-char cap reused — implemented, tested.
- T-09-SC: no new packages — honored (httpx/pytest only).

## Known stubs

None. All replies in tests are fully wired through the real orchestration path.

## Files

- Created: `backend/services/sarvam_client.py`, `backend/services/multilingual.py`, `backend/tests/test_multilingual_chat.py`
- Modified: `backend/schemas/chat.py`, `backend/api/routes.py`
- Explicitly untouched: `backend/services/agent.py` (frozen core)
