"""One-off live probe: multilingual round-trip through the real app + agent.

Usage: python scripts/live_multilingual_probe.py "<message>" "<location>" "<lang>"
Uses real Sarvam + OpenRouter keys from backend/.env. Mock nothing.
"""

import os
import sys

# Windows consoles default to cp1252, which cannot render Devanagari and
# crashes print() on Hindi replies. Force UTF-8 so multilingual output
# displays correctly instead of raising UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from main import app


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "Pune me mausam kaisa hai?"
    location = sys.argv[2] if len(sys.argv) > 2 else "Pune"
    language = sys.argv[3] if len(sys.argv) > 3 else "hi-IN"
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/chat",
        json={"message": message, "location": location, "language": language},
    )
    print("status=", resp.status_code)
    try:
        body = resp.json()
        print("alert_level=", body.get("alert_level"))
        print("language=", body.get("language"))
        print("reply=")
        print(str(body.get("reply", ""))[:2000])
    except Exception:
        print(resp.text[:1000])


if __name__ == "__main__":
    main()
