# Phase 4: Agent upgrade - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 4-Agent upgrade
**Areas discussed:** Grounding force, Location flow, Agri + climate, Degraded chat

---

## Grounding force

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt + tests | Stronger rules + mocked-LLM value-match tests | ✓ |
| Prompt only | Trust the model | |

**User's choice:** Prompt + tests

| Option | Description | Selected |
|--------|-------------|----------|
| Disclosure rules | Rewrite rule 6: cite non-IMD data + fallback notes | ✓ |
| Leave prompt | Disclosure in JSON only | |

**User's choice:** Disclosure rules

---

## Location flow

| Option | Description | Selected |
|--------|-------------|----------|
| One follow-up | Ask once, then best-effort answer | ✓ |
| Persist | Keep asking until resolved | |

**User's choice:** One follow-up

| Option | Description | Selected |
|--------|-------------|----------|
| No default | Always ask when unknown | ✓ |
| Default city | Assume e.g. Delhi with disclosure | |

**User's choice:** No default

---

## Agri + climate

| Option | Description | Selected |
|--------|-------------|----------|
| Curated + live | Static advisories + live weather grounding | ✓ |
| LLM knowledge | Pure model knowledge + tool output | |

**User's choice:** Curated + live

| Option | Description | Selected |
|--------|-------------|----------|
| Crops + seasons | Bounded scope | |
| Open-ended | Any agri/climate question, best effort | ✓ |

**User's choice:** Open-ended

---

## Degraded chat

| Option | Description | Selected |
|--------|-------------|----------|
| Graceful 200 | Data-unavailable message, still 200 | ✓ |
| Honest error | 502 like LLM outages | |

**User's choice:** Graceful 200 (tool-data path only; LLM fail-loudly unchanged)

| Option | Description | Selected |
|--------|-------------|----------|
| Name the gap | Which piece failed + what still works | ✓ |
| Generic | Something went wrong | |

**User's choice:** Name the gap

---

## Agent's Discretion

- Prompt wording, curated content/size, mocked-LLM harness shape.

## Deferred Ideas

None.
