# Phase 8: Climate trends - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 8-Climate trends (MoES gap-closure; user approved the fix proposal, then decided window + surface)

---

## Trend window

| Option | Description | Selected |
|--------|-------------|----------|
| 30-day anomaly | Past-30d aggregates vs own daily means + extremes | ✓ |
| Year compare | Same month last year side-by-side | |

**User's choice:** 30-day anomaly

## Landing surface

| Option | Description | Selected |
|--------|-------------|----------|
| Climate strip | Compact strip reusing showcase pattern | ✓ |
| Chat only | No landing change | |

**User's choice:** Climate strip

## Pre-approved proposal (no re-ask)

- Archive API (Open-Meteo, keyless, same seam); new `get_climate_trends` tool;
  agent rule + mocked-LLM tests; disclosure voice; MockTransport fixtures.

## Agent's Discretion

- JSON key names, strip layout, anomaly wording.

## Deferred Ideas

- Year-over-year; IMD cutover track unchanged.
