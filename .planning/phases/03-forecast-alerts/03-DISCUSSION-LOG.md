# Phase 3: Forecast + alerts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-09-11
**Phase:** 3-Forecast + alerts
**Areas discussed:** Forecast shape, Alert authority, Cache + fallback, Agent boundary

---

## Forecast shape

| Option | Description | Selected |
|--------|-------------|----------|
| New tool | New get_weather_forecast; current untouched | ✓ |
| Extend payload | Current + forecast bundle | |

**User's choice:** New tool

| Option | Description | Selected |
|--------|-------------|----------|
| 5-day full | date, min/max, rain %, condition, alert/day | ✓ |
| 3-day light | Same fields, 3 days | |

**User's choice:** 5-day full

---

## Alert authority

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse heuristic | Same derive_alert_level per day | ✓ |
| Stricter forecast | Uncertainty-discounted thresholds | |

**User's choice:** Reuse heuristic

| Option | Description | Selected |
|--------|-------------|----------|
| Worst-day line | Alert: Orange (Sat) | ✓ |
| Per-day only | No single line | |

**User's choice:** Worst-day line

| Option | Description | Selected |
|--------|-------------|----------|
| Per-day + rollup | Advisory per Orange/Red day + overall line | ✓ |
| Overall only | Single advisory | |

**User's choice:** Per-day + rollup

---

## Cache + fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Same 10-min | Keyed location+days | ✓ |
| Longer TTL | e.g. 1 hour | |

**User's choice:** Same 10-min

| Option | Description | Selected |
|--------|-------------|----------|
| Partial current | Current-only + unavailable note | ✓ |
| Full fallback | Mock forecast bundle | |

**User's choice:** Partial current

---

## Agent boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal wiring | Register tool + one-line prompt rule | ✓ |
| Tool only | No agent changes; wire in Phase 4 | |

**User's choice:** Minimal wiring

---

## Agent's Discretion

- Forecast JSON key names, rollup wording, days-parameter handling.

## Deferred Ideas

None.
