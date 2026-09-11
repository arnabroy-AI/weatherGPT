"""Hourly alert watcher over all 18 mapped cities (Phase 10, D-01/D-02/D-03).

Reads through the cached ``get_current_weather`` tool seam — ``derive_alert_level``
stays the sole threshold authority (this module never imports it and never
re-implements it). Dispatches Orange plus Red only, with one dispatch per
location-plus-level per 6 hours; severity upgrades re-fire immediately.

Trigger (planner decision): callable :func:`run_watch_cycle` plus
``POST /api/alerts/check`` as the documented hourly cron target, instead of
an in-process scheduler, because a scheduler would need a new dependency and
the cron-callable keeps the stdlib-only posture.

Security posture (T-10-04, T-10-05):
- Token material lives only in the in-memory registry; status/check
  responses carry counts plus at most a token suffix, never full tokens.
- A single-city failure is logged server-side and recorded as skipped —
  it never aborts the 18-city cycle.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Callable, Dict, List, Optional

from tools.weather import CITY_COORDS, get_current_weather

logger = logging.getLogger(__name__)

# D-01: all 18 mapped cities, hourly evaluation, Orange plus Red dispatch only.
# Derived from CITY_COORDS so the watcher can never drift from the tool map.
WATCH_CITIES: List[str] = [name.title() for name in CITY_COORDS]

# D-01 never-push rule: Green/Yellow never dispatch.
DISPATCH_LEVELS = frozenset({"Orange", "Red"})

# D-03: one dispatch per location-plus-level per 6 hours (21600 s).
COOLDOWN_S = 21600

# Severity ordering for the upgrade bypass (mirrors imd_client ordering;
# this module never calls derive_alert_level itself).
_SEVERITY = {"Green": 0, "Yellow": 1, "Orange": 2, "Red": 3}

# Registry validation bounds (D-02).
_MAX_TOKEN_CHARS = 2048
_MAX_TOPIC_CHARS = 128
_TOPIC_RE = re.compile(r"[A-Za-z0-9._~%-]+")

# Advisory body cap for dispatched notifications.
_MAX_BODY_CHARS = 200

# In-memory registry (D-02: no DB in v1). Lock-guarded set plus dict.
_tokens: set = set()
_topic_subs: Dict[str, set] = {}
_REGISTRY_LOCK = threading.Lock()

# Dedup state: per location-plus-level timestamp plus per-location
# last-level record (plus last-dispatch time for downgrade suppression).
_last_dispatch: Dict[tuple, float] = {}
_last_level: Dict[str, str] = {}
_last_time: Dict[str, float] = {}
_DEDUP_LOCK = threading.Lock()


def _require_token_shape(token: str) -> str:
    """Validate a device registration token; return it stripped."""
    cleaned = (token or "").strip()
    if not cleaned:
        raise ValueError("token must be a non-empty string.")
    if len(cleaned) > _MAX_TOKEN_CHARS:
        raise ValueError("token exceeds the maximum length of 2048 characters.")
    return cleaned


def _require_topic_shape(topic: str) -> str:
    """Validate an alert topic name; return it stripped.

    Tolerates and strips an optional ``/topics/`` prefix (same as the
    fcm_client seam), then enforces the FCM topic charset up to 128 chars.
    """
    cleaned = (topic or "").strip()
    if cleaned.startswith("/topics/"):
        cleaned = cleaned[len("/topics/"):]
    if (
        not cleaned
        or len(cleaned) > _MAX_TOPIC_CHARS
        or _TOPIC_RE.fullmatch(cleaned) is None
    ):
        raise ValueError(
            "topic must match [A-Za-z0-9._~%-] up to 128 characters."
        )
    return cleaned


def _normalize_loc_key(location: str) -> str:
    """Dedup key for a location: stripped-lower, never empty."""
    return (location or "Unknown").strip().lower() or "unknown"


def subscribe(token: str, topics) -> Dict[str, object]:
    """Register a device token against one or more alert topics.

    Args:
        token: Non-empty device registration token (max 2048 chars).
        topics: Non-empty list of topic names (each max 128 chars,
            FCM topic charset).

    Returns:
        Dict with the token suffix (last 6 chars, never the full token)
        plus the normalized topic list.

    Raises:
        ValueError: If the token or any topic fails validation.
    """
    cleaned_token = _require_token_shape(token)
    if topics is None or not isinstance(topics, (list, tuple)):
        raise ValueError("topics must be a non-empty list of topic names.")
    normalized = [_require_topic_shape(t) for t in topics]
    if not normalized:
        raise ValueError("topics must be a non-empty list of topic names.")
    # De-duplicate while preserving order.
    seen: set = set()
    unique: List[str] = []
    for name in normalized:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    with _REGISTRY_LOCK:
        _tokens.add(cleaned_token)
        for name in unique:
            _topic_subs.setdefault(name, set()).add(cleaned_token)
    return {"token_suffix": cleaned_token[-6:], "topics": unique}


def unsubscribe(token: str, topics=None) -> Dict[str, int]:
    """Remove a token from topics, or entirely when topics is None."""
    cleaned_token = _require_token_shape(token)
    if topics is not None:
        normalized = [_require_topic_shape(t) for t in topics]
    else:
        normalized = []
    with _REGISTRY_LOCK:
        if topics is None:
            _tokens.discard(cleaned_token)
            for subs in _topic_subs.values():
                subs.discard(cleaned_token)
        else:
            for name in normalized:
                subs = _topic_subs.get(name)
                if subs is not None:
                    subs.discard(cleaned_token)
        return registry_counts_locked()


def registry_counts_locked() -> Dict[str, int]:
    """Count snapshot assuming the caller already holds _REGISTRY_LOCK."""
    return {
        "tokens": len(_tokens),
        "topics": len(_topic_subs),
        "subscriptions": sum(len(subs) for subs in _topic_subs.values()),
    }


def registry_counts() -> Dict[str, int]:
    """Return token/topic/subscription counts (no token material)."""
    with _REGISTRY_LOCK:
        return registry_counts_locked()


def _tokens_for_topic(topic: str) -> List[str]:
    """Snapshot of tokens subscribed to a topic (internal, no token leak)."""
    with _REGISTRY_LOCK:
        return list(_topic_subs.get(topic, set()))


def evaluate_city(city: str) -> Optional[Dict[str, str]]:
    """Evaluate one city through the cached tool seam.

    Invokes the existing ``get_current_weather`` tool with the city name,
    parses its JSON string, and takes ``alert_level`` plus ``advisory`` plus
    ``location`` straight from the payload — no second heuristic here.

    Returns:
        Dict with ``location``/``alert_level``/``advisory``, or None on any
        failure (logged server-side) so one bad city never aborts the cycle.
    """
    try:
        raw = get_current_weather.invoke({"location": city})
        data = json.loads(raw)
        level = data.get("alert_level")
        location = data.get("location", city)
        advisory = data.get("advisory", "")
        return {
            "location": str(location or city),
            "alert_level": str(level) if level else "Unknown",
            "advisory": str(advisory or ""),
        }
    except Exception:
        logger.exception("alert watcher evaluate failed for city=%s", city)
        return None


def should_dispatch(location: str, alert_level: str, now: Optional[float] = None) -> bool:
    """Decide whether a location-plus-level alert should fire now.

    Monotonic-time dedup with a per location-plus-level timestamp plus a
    per-location last-level record: repeats inside the 21600 s cooldown stay
    silent, while a strictly-higher severity upgrade re-fires immediately.
    Green/Yellow (or unknown levels) never fire.

    A True return records the dispatch timestamp so the next call in the
    sequence observes it; False leaves state untouched.
    """
    level = (alert_level or "").strip()
    if level not in DISPATCH_LEVELS:
        return False
    loc_key = _normalize_loc_key(location)
    moment = time.monotonic() if now is None else float(now)
    new_sev = _SEVERITY.get(level, -1)
    with _DEDUP_LOCK:
        last = _last_level.get(loc_key)
        if last is None:
            _last_dispatch[(loc_key, level)] = moment
            _last_level[loc_key] = level
            _last_time[loc_key] = moment
            return True
        prev_sev = _SEVERITY.get(last, -1)
        if new_sev > prev_sev:
            _last_dispatch[(loc_key, level)] = moment
            _last_level[loc_key] = level
            _last_time[loc_key] = moment
            return True
        # Same-or-lower severity: suppress inside the cooldown window.
        stamped = _last_dispatch.get((loc_key, level))
        if stamped is not None:
            if moment - stamped < COOLDOWN_S:
                return False
        else:
            # Downgrade to a level never dispatched here: suppress while the
            # location's last dispatch (any level) is still inside cooldown.
            last_any = _last_time.get(loc_key)
            if last_any is not None and moment - last_any < COOLDOWN_S:
                return False
        _last_dispatch[(loc_key, level)] = moment
        _last_level[loc_key] = level
        _last_time[loc_key] = moment
        return True


def _slug_for_city(value: str) -> str:
    """Topic slug for a city/location display name."""
    slug = (value or "unknown").strip().lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-_.~%]", "-", slug)
    return slug.strip("-") or "unknown"


def _default_send(
    topic: str, title: str, body: str, alert_level: str, location: str
) -> str:
    """Default fan-out: topic send plus direct sends to subscribed tokens.

    The topic send must succeed; per-token sends are best-effort (logged
    and continued) so one bad registration never fails the cycle.
    """
    from services import fcm_client

    name = fcm_client.send_to_topic(topic, title, body, alert_level, location)
    for token in _tokens_for_topic(topic):
        try:
            fcm_client.send_to_token(token, title, body, alert_level, location)
        except Exception:
            logger.exception("alert watcher direct token send failed")
    return name


def run_watch_cycle(
    send_fn: Optional[Callable[[str, str, str, str, str], str]] = None,
    now: Optional[float] = None,
) -> Dict[str, object]:
    """Evaluate all 18 cities and dispatch Orange/Red with 6h dedup.

    Args:
        send_fn: Optional ``(topic, title, body, alert_level, location)``
            callable for tests; defaults to the fcm_client fan-out.
        now: Optional monotonic timestamp override for tests; defaults to
            ``time.monotonic()`` once per cycle.

    Returns:
        Dict with ``checked`` (int, always 18), ``dispatched`` (list of
        per-city entries) and ``skipped`` (list of per-city entries).
        Never raises on a single-city failure.
    """
    sender = send_fn if send_fn is not None else _default_send
    base_now = time.monotonic() if now is None else float(now)
    dispatched: List[Dict[str, object]] = []
    skipped: List[Dict[str, object]] = []
    for city in WATCH_CITIES:
        try:
            payload = evaluate_city(city)
        except Exception:
            logger.exception("alert watcher cycle evaluate failed for %s", city)
            skipped.append(
                {"city": city, "alert_level": None, "reason": "evaluate_failed"}
            )
            continue
        if payload is None:
            skipped.append(
                {"city": city, "alert_level": None, "reason": "evaluate_failed"}
            )
            continue
        level = payload.get("alert_level")
        location = payload.get("location", city)
        advisory = payload.get("advisory", "")
        if level not in DISPATCH_LEVELS:
            skipped.append(
                {"city": city, "alert_level": level, "reason": "below_threshold"}
            )
            continue
        # Snapshot dedup state so a failed send can roll back instead of
        # suppressing the next cycle for 6 hours.
        loc_key = _normalize_loc_key(str(location))
        with _DEDUP_LOCK:
            prev_dispatch = _last_dispatch.get((loc_key, str(level)))
            prev_level = _last_level.get(loc_key)
            prev_time = _last_time.get(loc_key)
        if not should_dispatch(str(location), str(level), now=base_now):
            skipped.append(
                {"city": city, "alert_level": level, "reason": "dedup_cooldown"}
            )
            continue
        topic = f"alerts-{_slug_for_city(str(location))}"
        title = f"WeatherGPT {level} alert for {location}"
        body = str(advisory or "")[:_MAX_BODY_CHARS]
        try:
            sender(topic, title, body, str(level), str(location))
        except Exception:
            logger.exception("alert watcher dispatch failed for %s", city)
            with _DEDUP_LOCK:
                if prev_dispatch is None:
                    _last_dispatch.pop((loc_key, str(level)), None)
                else:
                    _last_dispatch[(loc_key, str(level))] = prev_dispatch
                if prev_level is None:
                    _last_level.pop(loc_key, None)
                else:
                    _last_level[loc_key] = prev_level
                if prev_time is None:
                    _last_time.pop(loc_key, None)
                else:
                    _last_time[loc_key] = prev_time
            skipped.append(
                {"city": city, "alert_level": level, "reason": "send_failed"}
            )
            continue
        dispatched.append(
            {
                "city": city,
                "location": location,
                "alert_level": level,
                "topic": topic,
            }
        )
    return {"checked": len(WATCH_CITIES), "dispatched": dispatched, "skipped": skipped}


def reset_for_tests() -> None:
    """Clear registry plus dedup state (test isolation only)."""
    with _REGISTRY_LOCK:
        _tokens.clear()
        _topic_subs.clear()
    with _DEDUP_LOCK:
        _last_dispatch.clear()
        _last_level.clear()
        _last_time.clear()
