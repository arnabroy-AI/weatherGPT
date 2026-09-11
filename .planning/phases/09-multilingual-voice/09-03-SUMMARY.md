# Phase 09 Plan 03: Sarvam Secret-Safety + Coverage Matrix + Live Test — Summary

**Status:** complete
**Date:** 2026-09-11
**Requirements:** MULT-01, VOIC-01
**Commits:** 3b3112b, 8593076, 8fc0220

## One-liner

Sarvam key proven absent from errors, bodies, logs, and committed files by a 6-test sentinel suite; coverage matrix pins mayura:v1 / sarvam-translate:v1 / saaras:v3 / bulbul:v3 with the as-IN TTS OPT-OUT reason; one skipped-by-default live translate test; full suite 117 passed, 2 skipped with no new packages.

## Objective achieved

Sealed Phase 9 per D-06 key-never-logged plus the api-coverage contribution: the Sarvam integration is auditable (every translate/STT/TTS capability decided INTEGRATE vs OPT-OUT with pins, endpoints, header, and CI posture) and leak-proof (sentinel suite mirrors test_secrets.py across the multilingual chat path, the transcribe path, route bodies, and captured logs, plus a sanitize_detail unit check covering every route including both voice endpoints). CI stays fully mocked with exactly one tiny opt-in live test.

## Tasks completed

### Task 1 — Sarvam secret-safety tests plus env example — `3b3112b`

- `backend/tests/test_multilingual_secrets.py` (new, 6 tests): all three keys pointed at unique sentinels with cache clears, mirroring test_secrets.py discipline —
  - forced translate outage through the direct translate path (RuntimeError + logs clean),
  - forced translate outage through `POST /api/chat` hi-IN (502 body + logs clean),
  - forced STT outage through direct `transcribe_audio` (RuntimeError + logs clean),
  - forced STT outage through `POST /api/voice/transcribe` (502 body + logs clean),
  - LLM outage (`AgentExecutor.invoke` boom) mid-round-trip via real `process_multilingual_chat` with translate mocked (error + logs clean),
  - `sanitize_detail` unit check pinning Sarvam sentinel → `[REDACTED]` (sibling keys re-pinned).
- `backend/.env.example`: `SARVAM_API_KEY` placeholder line with never-commit comment + Sarvam dashboard location + docs link; no key material. Read-only flag cleared via `attrib -R` before editing (first action).
- Verified: `pytest tests/test_multilingual_secrets.py -q` → 6 passed; backend-tree scan finds the sentinel only in the test file itself and no live-looking key literals.

### Task 2 — Coverage matrix with pins plus OPT-OUT rows — `8593076`

- `.planning/phases/09-multilingual-voice/09-COVERAGE.md` (new): INTEGRATE rows for translate hi/mr/ta/te/bn-IN (`mayura:v1`), translate as-IN (`sarvam-translate:v1`), STT all six + en-IN (`saaras:v3`, mode transcribe, speech-to-text endpoint), TTS five Indic + en-IN (`bulbul:v3` / `shubh`, text-to-speech endpoint) — each with endpoint URL, `api-subscription-key` header, caps, MockTransport-only CI posture, and MULT-01/VOIC-01 requirement tags. OPT-OUT holds exactly the TTS as-IN row (Bulbul v3 has no as-IN entry → honest 422). Notes record 1000/2000 chunk limits, 2500-char TTS cap, 2MB audio cap, `numerals_format: international`, and frozen-agent-core wrapping.
- Verified: chat + voice suites → 21 passed; all four model pins grep-present.

### Task 3 — Opt-in live translate test plus full gate battery — `8fc0220`

- `backend/tests/test_live_sarvam.py` (new, exactly 1 test): tiny fixed text `What is the weather today` en-IN → hi-IN through the real `translate_text` path, module-level `skipif` on `RUN_LIVE_SARVAM != 1` plus in-test skip when no key; key captured at import, never logged/printed. Follows the pre-existing `test_live_openrouter.py` marker pattern with the plan-mandated `RUN_LIVE_SARVAM` flag.
- Verified: full battery `pytest tests/ -q` → **117 passed, 2 skipped** (Plan 01 baseline 99 passed/1 skipped + 12 voice + 6 secrets; second skip is the new live test, reported skipped by default). Collect-only confirms exactly one live Sarvam test. No dependency files touched (T-09-SC).

## Verification evidence

- `pytest tests/test_multilingual_secrets.py -q` → 6 passed.
- `pytest tests/test_multilingual_chat.py tests/test_multilingual_voice.py -q` → 21 passed.
- `pytest tests/ -q` → **117 passed, 2 skipped**.
- `pytest tests/test_live_sarvam.py -q -rs` → 1 skipped (gate message confirmed).
- Pin grep over 09-COVERAGE.md → mayura:v1, sarvam-translate:v1, saaras:v3, bulbul:v3 all present.
- Sentinel scan: `SENTINEL-7c3d9a1b2e4f` appears only in `test_multilingual_secrets.py`; no 40+-char key-like literals in backend source/tests/schemas/scripts.
- Package scan: `backend/requirements.txt` untouched; no pip/npm installs this phase.

## Deviations

None — plan executed exactly as written. No auto-fixes needed; the 09-02 `python-multipart` blocker was already resolved before this plan started (voice suites green at baseline).

## Threat model coverage

- T-09-10 (Sarvam key in outputs): mitigated — 5 outage-path tests prove absence from errors, bodies, logs; sanitize_detail unit check pins redaction.
- T-09-11 (key in committed files): mitigated — `.env.example` placeholder only; tree scan clean; real `.env` stays gitignored (untouched).
- T-09-12 (live test key handling): mitigated — gated on `RUN_LIVE_SARVAM=1`, tiny fixed text, key never printed/logged, skipped by default.
- T-09-SC (package installs): honored — no new packages; battery on vendored toolchain.

## Known stubs

None. All test replies/audio are fully wired through real orchestration with mocked provider responses; the live test asserts a non-empty real translation on its opt-in path.

## Files

- Created: `backend/tests/test_multilingual_secrets.py`, `backend/tests/test_live_sarvam.py`, `.planning/phases/09-multilingual-voice/09-COVERAGE.md`
- Modified: `backend/.env.example` (SARVAM_API_KEY placeholder block only)
- Explicitly untouched: `backend/services/agent.py` (frozen core), `backend/requirements.txt` (no new packages), all frontend files

## Self-Check: PASSED

- 09-03-SUMMARY.md exists on disk; all three task commits (`3b3112b`, `8593076`, `8fc0220`) resolve in `git log`.
- Only the plan's `files_modified` plus the SUMMARY were staged/committed; pre-existing worktree modifications (`backend/core/config.py`, `backend/scripts/live_chat_probe.py`, etc.) left untouched.
