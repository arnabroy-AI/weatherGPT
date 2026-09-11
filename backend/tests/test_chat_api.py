"""Tracer tests: mocked POST /api/chat end-to-end plus /health liveness.

The LLM is kept out of the suite by patching ``process_chat`` inside the
``api.routes`` namespace (the route uses a from-import binding, so patching
``services.agent.process_chat`` alone would have no effect on the route).
"""

from unittest.mock import patch

import httpx
import pytest

from main import app


@pytest.mark.asyncio
async def test_chat_mocked_end_to_end():
    """Mocked agent returns 200 with reply + alert_level for 'Hi in Mumbai'."""
    fake_result = {
        "reply": "Sunny in Mumbai, 29.5 C. Light rain possible.\nAlert: Green",
        "alert_level": "Green",
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        with patch("api.routes.process_chat", return_value=fake_result) as fake:
            response = await client.post(
                "/api/chat",
                json={"message": "Hi in Mumbai", "location": "Mumbai"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == fake_result["reply"]
    assert body["alert_level"] == "Green"
    fake.assert_called_once_with(message="Hi in Mumbai", location="Mumbai")


@pytest.mark.asyncio
async def test_health_liveness_shape():
    """GET /health returns the liveness shape {status, app, version}."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app" in body
    assert "version" in body
