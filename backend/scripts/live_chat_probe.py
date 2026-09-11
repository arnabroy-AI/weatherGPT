"""One-off live probe: POST one chat query through the real app + agent.

Usage: python scripts/live_chat_probe.py "<message>" "<location>"
Never committed with keys; reads .env like production.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from main import app


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "Current weather in Pune"
    location = sys.argv[2] if len(sys.argv) > 2 else "Pune"
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/chat", json={"message": message, "location": location})
    print("status=", resp.status_code)
    try:
        body = resp.json()
        print("alert_level=", body.get("alert_level"))
        print("reply=")
        print(body.get("reply", "")[:2000])
    except json.JSONDecodeError:
        print(resp.text[:1000])


if __name__ == "__main__":
    main()
