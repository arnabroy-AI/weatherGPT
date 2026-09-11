# Phase 9: Multilingual voice + chat - Discussion Log

> **Audit trail only.**

**Date:** 2026-09-11
**Phase:** 9-Multilingual voice + chat
**Areas discussed:** Languages, Voice shape, Translation scope (compressed — credentials already live)

---

## Languages

| Option | Description | Selected |
|--------|-------------|----------|
| Hindi | First-class | ✓ |
| Marathi | | ✓ |
| Tamil | | ✓ |
| Telugu | | ✓ |

**User's choice:** Above + "Add bengali and assames language too" → bn-IN, as-IN (verify support, else honest fallback)

## Voice shape

| Option | Description | Selected |
|--------|-------------|----------|
| Backend only | STT/TTS endpoints, no mic UI | ✓ |
| Include mic UI | Frontend button now | |

**User's choice:** Backend only

## Translation scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full round-trip | Query→EN→agent→reply back | ✓ |
| Facts only | Advisories stay English | |

**User's choice:** Full round-trip

---

## Agent's Discretion

- Model pins, audio formats/limits, TTS voices.

## Deferred Ideas

- Mic UI; SMS/WhatsApp; year-compare.
