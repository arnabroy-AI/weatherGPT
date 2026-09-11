# Phase 2: IMD live data - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-11
**Phase:** 2-IMD live data
**Areas discussed:** IMD source, Cache policy, Fallback mode, Location map

---

## IMD source

| Option | Description | Selected |
|--------|-------------|----------|
| You provide access | User gives endpoint + credentials | |
| Researcher picks | Researcher finds best public IMD endpoint | ✓ (via freeform: "no i dont have any IMD endpoint") |

**User's choice:** Researcher picks (user has no endpoint)
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Key required | WEATHER_API_KEY is the IMD credential; missing → 502 | ✓ |
| Key optional | Work without key where possible | |

**User's choice:** Key required
**Notes:** Required-semantics kept, but must work keyless when source allows.

| Option | Description | Selected |
|--------|-------------|----------|
| Prefer keyless | Researcher prefers free public IMD endpoints | ✓ |
| Allow key-gated | Researcher may pick gated APIs needing real key | |

**User's choice:** Prefer keyless
**Notes:** —

---

## Cache policy

| Option | Description | Selected |
|--------|-------------|----------|
| Memory 10-min | In-memory TTL, per normalized location | ✓ |
| Persistent | Disk/sqlite surviving restarts | |

**User's choice:** Memory 10-min
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Stale-serve | Serve stale + background refresh | |
| Stale-on-error | Stale only when IMD errors | |

**User's choice:** "choose anyone which fits well" → agent's discretion
**Notes:** Planner picks; recorded under Claude's Discretion.

---

## Fallback mode

| Option | Description | Selected |
|--------|-------------|----------|
| Mock fallback | Outage → mock JSON stamped as fallback | ✓ |
| Cache fallback | Outage → last-known cached data | |
| Honest 502 | Outage → 502 like the LLM path | |

**User's choice:** Mock fallback
**Notes:** IMD path only; LLM errors stay fail-loudly per Phase 1 D-06.

| Option | Description | Selected |
|--------|-------------|----------|
| Disclose always | Reply notes fallback/stale data | ✓ |
| Silent | Source field only, clean answer | |

**User's choice:** Disclose always
**Notes:** —

---

## Location map

| Option | Description | Selected |
|--------|-------------|----------|
| Curated map | In-code city→station map | ✓ |
| Pass through | Free text straight to IMD | |

**User's choice:** Curated map
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Ask follow-up | Unknown → tool Unknown JSON, agent clarifies | |
| Best guess | Nearest station + disclose the guess | ✓ |

**User's choice:** Best guess
**Notes:** —

---

## Agent's Discretion

- Stale-cache serving strategy (D-03 detail).

## Deferred Ideas

None.
