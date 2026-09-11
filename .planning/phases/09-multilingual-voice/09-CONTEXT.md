# Phase 9: Multilingual voice + chat - Context

**Gathered:** 2026-09-11
**Status:** Ready for planning

## Phase Boundary

Sarvam-powered multilingual chat + voice endpoints on the backend. Translate query→English→agent→reply back; STT + TTS endpoints; per-language capability map with graceful fallback. No frontend mic UI (later), no new providers, English core untouched.

## Implementation Decisions

### Languages
- **D-01:** Six languages: Hindi (hi-IN, first-class), Marathi (mr-IN), Tamil (ta-IN), Telugu (te-IN), Bengali (bn-IN), Assamese (as-IN).
- **D-02:** Per-language capability map in code: if Sarvam lacks a model voice/translation for a code (verify Assamese + Bengali at plan time against Sarvam docs), that language degrades to an honest unsupported message — never a crash, never silent English substitution without disclosure.

### Translation shape
- **D-03:** Full round-trip: user query → English (Sarvam translate) → frozen agent core → full reply translated back to the user's language. Numbers/alert levels must survive translation byte-identical where feasible (assert in tests).
- **D-04:** Language resolved per request (`language` field, default English). New `POST /api/chat` optional field — response gains optional `language` echo; existing clients unaffected.

### Voice shape
- **D-05:** Backend-only endpoints: `POST /api/voice/transcribe` (audio upload → text + detected language) and `POST /api/voice/speak` (text + language → audio bytes). No frontend mic/playback in Phase 9.
- **D-06:** Audio size caps + content-type allowlist; Sarvam failures map to safe 502s (log-full/send-safe); key never logged.

### Claude's Discretion
- Sarvam model pins (saarika/bulbul/mayura versions), audio formats, char limits, TTS voice picks.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contracts
- Sarvam API (key VERIFIED live 2026-09-11, `HTTP 200` on translate): `https://api.sarvam.ai/translate` (header `api-subscription-key`), `/speech-to-text` (Saarika), `/text-to-speech` (Bulbul). Confirm exact model names + as-IN/bn-IN support at https://docs.sarvam.ai during planning.
- `backend/.env`: `SARVAM_API_KEY` live. Never log it; secret-safety tests mandatory.
- `services/agent.py` (frozen core — translate around it, never inside), `api/routes.py` (new endpoints follow existing error mapping), `schemas/chat.py` (optional `language` field).
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md` (MULT-01, VOIC-01), `.planning/ROADMAP.md` (Phase 9 criteria).

## Existing Code Insights

### Reusable Assets
- `process_chat(message, location)` — the frozen English core; multilingual wraps its inputs/outputs.
- Route error mapping (422/502/500) + `sanitize_detail` + key redaction — voice endpoints reuse verbatim.
- MockTransport + mocked-LLM test philosophy — Sarvam HTTP mocked in CI; one opt-in live test max (tiny text, like the vendor probe).
- Throttle (60/min) applies to new POST endpoints automatically if mounted on the same router.

### Established Patterns
- Tool/JSON contracts, disclosure voice (extend to translation notes: "translated from English" where honest).
- `attrib -R` before editing R-flagged files; temp-dir frontend builds (untouched this phase).

### Integration Points
- New `services/sarvam_client.py` (translate/stt/tts thin client) + routes + schema field; agent core untouched.
- Phase 10 (push) will reuse language prefs for alert copy — keep language codes canonical.

## Specific Ideas

User's language list verbatim: Hindi, Marathi, Tamil, Telugu + Bengali + Assamese.

## Deferred Ideas

- Frontend mic button + audio playback → later frontend slice. SMS/WhatsApp → Phase 10+ (needs keys). Same-month-last-year → rejected earlier.

---

*Phase: 9-Multilingual voice + chat*
*Context gathered: 2026-09-11*
