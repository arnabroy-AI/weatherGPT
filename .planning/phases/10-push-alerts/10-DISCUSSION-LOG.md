# Phase 10: Proactive push alerts - Discussion Log

> **Audit trail only.**

**Date:** 2026-09-11
**Phase:** 10-Proactive push alerts
**Areas discussed:** Watcher, Targets, Dedup (compressed)

---

## Watcher

| Option | Description | Selected |
|--------|-------------|----------|
| 18 cities hourly | All mapped cities, hourly, Orange+Red | ✓ |
| Short list | 3 demos, 15-min | |

**User's choice:** 18 cities hourly

## Targets

| Option | Description | Selected |
|--------|-------------|----------|
| Send + subscribe | Token + topic send; registration endpoints | ✓ |
| Topics only | Broadcast, no registration | |

**User's choice:** Send + subscribe

## Dedup

| Option | Description | Selected |
|--------|-------------|----------|
| 6h cooldown | Per location+level; upgrades re-fire | ✓ |
| No dedup | Every breach fires | |

**User's choice:** 6h cooldown

---

## Agent's Discretion

- FCM library vs raw httpx; payload shape; registry structure; trigger mechanism.

## Deferred Ideas

- SMS/WhatsApp; subscribe UI; persistent registry.
