"""Per-IP sliding-window rate limiter for POST /api/chat (Phase 7, D-06).

Stdlib only (``time.monotonic`` + ``threading.Lock``): no new dependencies.
Single-node SIH demo: keyed on ``request.client.host`` only, never on
``X-Forwarded-For`` (spoofable; accepted limitation T-07-01).

Callers map the returned ``retry_after_secs`` to the ``Retry-After``
response header on HTTP 429.
"""

import math
import threading
import time

_WINDOW_SECONDS = 60.0
_DEFAULT_LIMIT_PER_MIN = 60

_lock = threading.Lock()
_hits: dict = {}


def _current_limit() -> int:
    """Read the throttle limit from settings on every call (env-overridable)."""
    try:
        from core.config import get_settings

        return int(get_settings().CHAT_THROTTLE_PER_MIN)
    except Exception:
        return _DEFAULT_LIMIT_PER_MIN


def check_rate_limit(client_ip: str) -> tuple:
    """Record a hit for ``client_ip``; return ``(allowed, retry_after_secs)``.
    Sliding window of ``_WINDOW_SECONDS``: at most ``CHAT_THROTTLE_PER_MIN``
    hits per window. When over the limit, ``allowed`` is False and
    ``retry_after_secs`` is the whole seconds until the oldest hit in the
    window expires (minimum 1). Unknown/empty IPs share one bucket so they
    are still throttled rather than exempt.
    """
    now = time.monotonic()
    limit = _current_limit()
    key = client_ip or "unknown"
    with _lock:
        bucket = [t for t in _hits.get(key, []) if now - t < _WINDOW_SECONDS]
        if len(bucket) >= limit:
            oldest = min(bucket) if bucket else now
            retry_after = max(1, int(math.ceil(_WINDOW_SECONDS - (now - oldest))))
            _hits[key] = bucket
            return False, retry_after
        bucket.append(now)
        _hits[key] = bucket
        return True, 0


def reset_rate_limiter() -> None:
    """Clear all throttle buckets (test isolation; wired into conftest)."""
    with _lock:
        _hits.clear()
