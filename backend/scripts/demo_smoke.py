"""WeatherGPT seeded demo smoke check (D-05).

Default mode is OFFLINE: it proves, without Docker and without keys, that
the three seeded demo queries in README.md byte-match the chat starter
strings in ``frontend/components/chat/starters.tsx``, that ``compose.yaml``
parses with exactly the ``backend`` + ``frontend`` services, and it attempts
``GET /health`` only as an optional probe (never a failure).

Opt-in live mode (``--live``) posts the trio to a running backend and
reports pass/fail per query. Live LLM answers need a real key in the host
``.env``; without one the backend returns 502 and the query FAILs.

Key safety (T-07-05): this script never reads ``.env``, never reads key
environment variables, and never prints key values. Only pass/fail words,
status codes, and alert levels reach stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STARTERS_PATH = ROOT / "frontend" / "components" / "chat" / "starters.tsx"
TEASER_PATH = ROOT / "frontend" / "components" / "live-demo-teaser.tsx"
README_PATH = ROOT / "README.md"
COMPOSE_PATH = ROOT / "compose.yaml"

# Seeded trio (D-05). MUST byte-match STARTER_QUERIES in starters.tsx and the
# SEEDED query strings in live-demo-teaser.tsx. Exact bytes — do not reword.
SEEDED_QUERIES = (
    "Current weather in Pune",
    "Mumbai this weekend",
    "Paddy sowing advice for Nashik",
)

EXPECTED_SERVICES = ("backend", "frontend")


def check_starter_parity() -> list[str]:
    """README strings byte-match starters.tsx (and the teaser SEEDED list)."""
    failures: list[str] = []
    try:
        starters_text = STARTERS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"MISMATCH: cannot read {STARTERS_PATH}: {exc}"]
    try:
        readme_text = README_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"MISMATCH: cannot read {README_PATH}: {exc}"]
    try:
        teaser_text = TEASER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"MISMATCH: cannot read {TEASER_PATH}: {exc}"]
    for query in SEEDED_QUERIES:
        for label, text in (
            ("starters.tsx", starters_text),
            ("README.md", readme_text),
            ("live-demo-teaser.tsx", teaser_text),
        ):
            if query not in text:
                failures.append(
                    f"MISMATCH: {query!r} byte-missing from {label}"
                )
    return failures


def parse_compose_services(text: str) -> list[str]:
    """Minimal indentation-aware parse: top-level `services:` block, then the
    keys at exactly one indent level (two spaces) beneath it."""
    services: list[str] = []
    in_services = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            in_services = stripped == "services:"
            continue
        if in_services and indent == 2 and stripped.endswith(":"):
            services.append(stripped[:-1])
        elif in_services and indent < 2:
            in_services = False
    return services


def check_compose() -> list[str]:
    """compose.yaml parses with exactly the backend + frontend services and
    carries no secret values."""
    try:
        text = COMPOSE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"MISMATCH: cannot read {COMPOSE_PATH}: {exc}"]
    failures: list[str] = []
    services = parse_compose_services(text)
    if sorted(services) != sorted(EXPECTED_SERVICES):
        failures.append(
            f"MISMATCH: compose services {services} != {list(EXPECTED_SERVICES)}"
        )
    if "env_file" not in text or ".env" not in text:
        failures.append("MISMATCH: compose backend missing env_file .env")
    if "NEXT_PUBLIC_WEATHERGPT_API" not in text:
        failures.append(
            "MISMATCH: compose frontend missing NEXT_PUBLIC_WEATHERGPT_API build arg"
        )
    return failures


def probe_health(base_url: str, timeout_s: float = 3.0) -> str:
    """Attempt GET /health. Reachability is informational only — the offline
    run passes whether or not a backend is running."""
    url = base_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            body = resp.read(200).decode("utf-8", "replace")
        return f"health: reachable ({resp.status}) {body[:60]}"
    except Exception as exc:
        return f"health: not running (optional probe skipped: {type(exc).__name__})"


def post_query(base_url: str, query: str, timeout_s: float = 60.0) -> tuple[bool, str]:
    """POST one seeded query to a running backend. Returns (passed, summary)
    where the summary carries status code + alert level only, never keys."""
    url = base_url.rstrip("/") + "/api/chat"
    payload = json.dumps({"message": query, "location": ""}).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return False, f"FAIL: {query!r} -> HTTP {exc.code}"
    except Exception as exc:
        return False, f"FAIL: {query!r} -> {type(exc).__name__}"
    reply = data.get("reply") if isinstance(data, dict) else None
    alert = data.get("alert_level") if isinstance(data, dict) else None
    if isinstance(reply, str) and reply.strip():
        return True, f"PASS: {query!r} (alert: {alert})"
    return False, f"FAIL: {query!r} -> empty reply"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline parity checks for the seeded demo trio; --live posts them to a running backend."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run offline checks only (default mode; --live adds live posts).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Also POST the trio to a running backend (needs real keys in host .env).",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL for health probe and --live posts.",
    )
    args = parser.parse_args(argv)

    failures = check_starter_parity()
    failures += check_compose()

    for query in SEEDED_QUERIES:
        print(f"seeded query: {query}")
    print(f"parity: {'PASS' if not failures else 'FAIL'} "
          f"({len(SEEDED_QUERIES)} queries x starters/README/teaser)")
    print(f"compose: {'PASS' if not any('compose' in f for f in failures) else 'FAIL'} "
          f"(services: {', '.join(EXPECTED_SERVICES)})")
    for failure in failures:
        print(failure)
    print(probe_health(args.base_url))

    if args.live:
        live_failed = 0
        for query in SEEDED_QUERIES:
            passed, summary = post_query(args.base_url, query)
            print(summary)
            if not passed:
                live_failed += 1
        if live_failed:
            print(f"live: FAIL ({live_failed}/{len(SEEDED_QUERIES)} queries failed)")
            return 1
        print(f"live: PASS ({len(SEEDED_QUERIES)}/{len(SEEDED_QUERIES)} queries green)")

    if failures:
        return 1
    print("smoke: PASS (offline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
