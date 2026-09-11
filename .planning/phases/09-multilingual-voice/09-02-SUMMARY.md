# Phase 09 Plan 02: Six-Language Voice Expansion — Summary

**Status:** blocked (1 of 3 tasks committed; Tasks 2–3 implemented but unverifiable)
**Date:** 2026-09-11
**Requirements:** MULT-01, VOIC-01 (remainder — not marked complete)
**Commits:** 9fa097c (Task 1 only)

## One-liner

Six-language capability map plus Saaras STT and Bulbul TTS clients landed (Task 1, committed); voice endpoints plus full test file are written but cannot execute because `python-multipart` is absent from the environment and plan deviation rules forbid the executor from installing packages without human legitimacy verification.

## Objective status

Partially achieved. The D-02 capability map, per-language translate routing
(as-IN → `sarvam-translate:v1`, other five → `mayura:v1`), STT (`saaras:v3`)
and TTS (`bulbul:v3` / `shubh`) clients, and the multilingual TTS gate are
implemented and regression-clean against the Plan 01 suite. The D-05/D-06
voice endpoints and the D-02/D-03/D-06 test file are implemented to spec but
**unverified**: importing `api.routes` (hence `main.app`, hence every test)
fails at route-registration time because FastAPI `File`/`Form` require
`python-multipart`, which is not installed and not in `requirements.txt`.

## Tasks completed

### Task 1 — STT plus TTS clients with per-language capability map — `9fa097c` ✅

- `backend/services/sarvam_client.py`: `CAPABILITIES` table (hi/mr/ta/te/bn-IN →
  `mayura:v1`, STT+TTS; as-IN → `sarvam-translate:v1`, STT-only, TTS explicitly
  unsupported), `translate_model_for` routing with 1000/2000-char chunk limits,
  `transcribe_audio` (multipart file + `saaras:v3` + `language_code` + mode
  `transcribe` → `(transcript, language_code)` tuple), `synthesize_speech`
  (JSON text/language/`bulbul:v3`/`shubh` → base64-decoded first `audios`
  entry), sanitized `RuntimeError` throughout, key never in exceptions,
  server-side-only logging, shared transport seam kept.
- `backend/services/multilingual.py`: `TTS_SUPPORTED_LANGUAGES` derived from
  the capability map plus `en-IN`; `require_tts_supported` raising the honest
  English no-voice-yet message for as-IN (lists hi-IN mr-IN ta-IN te-IN bn-IN
  en-IN); `process_chat` internals untouched.
- Verified: `pytest tests/test_multilingual_chat.py -q` → **9 passed**
  (hi-IN still pins `mayura:v1`, chunking intact). Committed as `9fa097c`.

### Task 2 — Voice endpoints with caps, allowlist, throttle, error mapping — ⚠️ written, uncommitted

- `backend/schemas/chat.py`: `SpeakRequest` (text 1–2500 chars + language,
  default `en-IN`) and `TranscribeResponse` (transcript + language_code).
- `backend/api/routes.py`: `POST /api/voice/transcribe` (multipart audio +
  `language_code` Form default `unknown`; 2MB cap → 413, ten-type allowlist →
  422, same per-IP throttle with `Retry-After`, `run_in_threadpool` into
  `transcribe_audio`, ValueError→422 / RuntimeError→502 / generic→500 via the
  existing mapping) and `POST /api/voice/speak` (JSON → `synthesize_speech`
  → raw `audio/wav`; as-IN → honest 422 translated to as-IN via the
  `sarvam-translate:v1` path with English fallback; same throttle + mapping).
  No frontend files touched. `process_chat` and agent internals untouched.
- Syntax-checked (`py_compile` OK) but **unverifiable and uncommitted** (see Blocker).

### Task 3 — Language-row plus voice round-trip plus cap tests — ⚠️ written, uncommitted

- `backend/tests/test_multilingual_voice.py` (new, 12 tests): parametrized
  mr/ta/te/bn/as-IN chat rows with digit preservation, as-IN vs hi-IN model
  routing assertion (`sarvam-translate:v1` / `mayura:v1`), transcribe
  round-trip, speak round-trip (`audio/wav`, byte-exact), as-IN speak 422
  naming as-IN with zero TTS hits, 3MB → 413 with zero provider calls,
  `text/plain` → 422, forced STT outage → sanitized 502. All mocked, no live
  network by construction.
- `pytest tests/test_multilingual_voice.py tests/test_chat_api.py -q` →
  **collection ERROR** (see Blocker). Uncommitted.

## Blocker (Rule 3 package-install exclusion + Rule 4 contract dependency)

**Missing package: `python-multipart` — human verification required before install.**

- **Evidence:** `import multipart` → `ModuleNotFoundError`; `pip show
  python-multipart` → not found; absent from `backend/requirements.txt`.
  `pytest tests/test_multilingual_voice.py tests/test_chat_api.py -q` fails in
  collection with `RuntimeError: Form data requires "python-multipart" to be
  installed`, raised from `api/routes.py` route registration — this breaks
  `main.app` import, so the **entire suite** cannot run with Task 2 code present.
- **Why not auto-fixed:** executor deviation Rule 3 explicitly excludes
  package-manager installs — a missing package may indicate slopsquatting or a
  hallucinated name, so the executor must not `pip install` an alternative or
  retry under another name. The plan's threat model (T-09-SC) assumed "no new
  packages", so this is new information requiring a human decision.
- ** maps to threats:** T-09-05/T-09-06 mitigations (multipart upload caps +
  allowlist) cannot execute until the multipart parser exists.
- **To unblock (human):**
  1. Verify legitimacy: https://pypi.org/project/python-multipart/
     (canonical FastAPI-documented multipart parser, Andrew Dunham —
     confirms this is not a slopsquat).
  2. Install: `pip install python-multipart` (optionally pin in
     `backend/requirements.txt` — note: that file is OUTSIDE this plan's
     `files_modified`, so the resuming agent should treat the pin as a
     Rule-2-adjacent fix or leave it to the human).
  3. Resume: `python -m pytest tests/test_multilingual_voice.py
     tests/test_chat_api.py -q`, then full `python -m pytest tests/ -q`,
     then commit Tasks 2–3 atomically per the plan's commit protocol.
- **Alternative (human):** replan transcribe as raw-body upload instead of
  multipart — architectural change (Rule 4), needs `/gsd-plan-phase` rework.

## Verification evidence

- `pytest tests/test_multilingual_chat.py -q` (post-Task-1) → **9 passed**
  (Plan 01 baseline preserved: `mayura:v1` shape, missing-key/non-200
  sanitization, chunking, Hindi round-trip digits, English passthrough).
- `pytest tests/test_multilingual_voice.py tests/test_chat_api.py -q` →
  **collection ERROR** (`python-multipart` missing; output above).
- Full suite `pytest tests/ -q` → **not run to green** (blocked by the same
  import failure; last green baseline remains Plan 01: 99 passed, 1 skipped).
- `py_compile` on all five plan files → OK.
- No live network: all new code paths go through the `MockTransport` seam;
  the sentinel `test-sarvam-key` is the only key referenced in tests.

## Deviations

None applied — no auto-fix was permissible (package installs are excluded
from Rule 3). Task 2/3 code is held uncommitted rather than committing
import-breaking changes onto `main`.

## Threat model coverage

- T-09-05 (2MB cap → 413 before provider): implemented, unproven (blocked).
- T-09-06 (ten-type allowlist → 422): implemented, unproven (blocked).
- T-09-07 (provider-side detection via `unknown` default, echo without trust):
  implemented, unproven (blocked).
- T-09-08 (sanitized 502s, key never in bodies/logs): implemented in clients;
  route-level proof blocked.
- T-09-09 (same throttle + `Retry-After` on both endpoints): implemented,
  unproven (blocked).
- T-09-SC: no package installed by the executor — honored (this block exists
  because of it).

## Known stubs

None. All replies/audio in tests are fully wired through mocked provider
responses (no empty/mock-data-to-UI paths).

## Files

- Committed (`9fa097c`): `backend/services/sarvam_client.py`,
  `backend/services/multilingual.py`
- Written, uncommitted (blocked): `backend/api/routes.py`,
  `backend/schemas/chat.py`, `backend/tests/test_multilingual_voice.py`
- Explicitly untouched: `backend/services/agent.py` (frozen core),
  all frontend files (D-05 backend-only scope)
