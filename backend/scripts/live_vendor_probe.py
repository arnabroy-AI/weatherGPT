"""One-off live probe: verify SARVAM_API_KEY + FCM service-account shape.

Usage: python scripts/live_vendor_probe.py [--sarvam] [--fcm]
Sarvam: tiny en-IN -> hi-IN translation (auth proof, not a feature test).
FCM: structural validation only (live send needs a device token, Phase 10).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_sarvam() -> None:
    import httpx

    from core.config import get_settings

    key = get_settings().SARVAM_API_KEY if hasattr(get_settings(), "SARVAM_API_KEY") else ""
    if not key:
        print("sarvam: NO KEY CONFIGURED")
        return
    try:
        resp = httpx.post(
            "https://api.sarvam.ai/translate",
            headers={"api-subscription-key": key},
            json={
                "input": "What is the weather today?",
                "source_language_code": "en-IN",
                "target_language_code": "hi-IN",
            },
            timeout=30.0,
        )
    except Exception as exc:
        print(f"sarvam: TRANSPORT FAIL {exc}")
        return
    print("sarvam: HTTP", resp.status_code)
    safe = resp.text[:600].encode("ascii", errors="replace").decode("ascii")
    print(safe)
    if resp.status_code == 401:
        print("sarvam: KEY REJECTED")
    elif resp.status_code == 200:
        print("sarvam: KEY LIVE")


def check_fcm() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "fcm-service-account.json"),
        os.environ.get("FCM_SERVICE_ACCOUNT_FILE", ""),
    ]
    path = next((c for c in candidates if c and os.path.exists(c)), None)
    if not path:
        print("fcm: FILE NOT FOUND")
        return
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = required - set(data.keys())
    print("fcm: project_id =", data.get("project_id"))
    print("fcm: client_email =", data.get("client_email"))
    print("fcm: key looks PEM =", str(data.get("private_key", "")).startswith("-----BEGIN"))
    if missing:
        print("fcm: MISSING KEYS", sorted(missing))
    else:
        print("fcm: SHAPE VALID (live send needs a device token — Phase 10)")


if __name__ == "__main__":
    if "--sarvam" in sys.argv:
        check_sarvam()
    if "--fcm" in sys.argv:
        check_fcm()
    if len(sys.argv) == 1:
        check_sarvam()
        check_fcm()
