# Phase 9: Multilingual voice + chat — API coverage matrix

**Phase:** 09-multilingual-voice · **Date:** 2026-09-11
**Engine:** Sarvam AI (translate + Saaras STT + Bulbul TTS) wrapped around the
frozen English agent core (D-03): user query → English → `process_chat`
→ reply translated back; alert level derived pre-translation.
CI posture: `httpx.MockTransport` plus mocked LLM only, with one tiny opt-in
live translate test maximum (`tests/test_live_sarvam.py`, skipped by default).

## INTEGRATE

| Capability | Status | Requirement | Scope note |
|------------|--------|-------------|------------|
| Translate hi-IN / mr-IN / ta-IN / te-IN / bn-IN via `mayura:v1` | INTEGRATE | MULT-01 | `POST https://api.sarvam.ai/translate`, header `api-subscription-key`, `numerals_format: international` so digits survive byte-identical; 1000-char sentence-boundary chunking; MockTransport-only in CI. |
| Translate as-IN (either side of the pair) via `sarvam-translate:v1` | INTEGRATE | MULT-01 | Same translate endpoint + header; covers all 22 scheduled languages; 2000-char chunking; MockTransport-only in CI. |
| STT for hi-IN / mr-IN / ta-IN / te-IN / bn-IN / as-IN / en-IN via `saaras:v3` | INTEGRATE | VOIC-01 | `POST https://api.sarvam.ai/speech-to-text`, header `api-subscription-key`, multipart `file` + `language_code` + `mode: transcribe`; `POST /api/voice/transcribe` (2MB cap → 413, ten-type allowlist → 422 before any provider call); MockTransport-only in CI. |
| TTS for hi-IN / mr-IN / ta-IN / te-IN / bn-IN / en-IN via `bulbul:v3` speaker `shubh` | INTEGRATE | VOIC-01 | `POST https://api.sarvam.ai/text-to-speech`, header `api-subscription-key`, JSON text/language/model/speaker, 2500-char schema cap; `POST /api/voice/speak` returns raw `audio/wav`; MockTransport-only in CI. |

## OPT-OUT

| Capability | Status | Requirement | Reason |
|------------|--------|-------------|--------|
| TTS for as-IN | OPT-OUT | VOIC-01 | Bulbul v3 supports 11 languages with no as-IN entry, so `POST /api/voice/speak` returns an honest 422 naming as-IN (message translated to as-IN via `sarvam-translate:v1` when available, English otherwise) — never silent substitution, never a crash. |

## Notes

- Chunk limits: 1000 chars per request on `mayura:v1`, 2000 on
  `sarvam-translate:v1` (split at sentence boundaries; short inputs pass
  through byte-identical).
- TTS input cap: 2500 characters (schema-enforced); audio upload cap: 2MB
  (route-enforced before any provider contact).
- `numerals_format: international` on every translate call keeps digits and
  alert-relevant numbers byte-identical across the round-trip.
- Frozen-agent-core wrapping: `services/agent.py` untouched — multilingual
  orchestration lives in `services/multilingual.py` around it.
- Key posture (D-06): `SARVAM_API_KEY` travels only on the outbound
  `api-subscription-key` header; failures are logged server-side and surfaced
  as sanitized errors (`sanitize_detail` redacts on every route including both
  voice endpoints); sentinel suite in `tests/test_multilingual_secrets.py`.
