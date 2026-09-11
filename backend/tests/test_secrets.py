"""Secret-safety tests: key material never leaks into logs or responses (D-17).

Sets both key env vars to sentinel markers, clears both caches, forces an LLM
failure through the real agent path (executor.invoke raising, as a provider
outage would), then asserts neither sentinel appears in the raised error, the
HTTP response body, or captured log output.
"""

import logging

import httpx
import pytest

from main import app
from services import agent as agent_module

SENTINEL_OPENROUTER = "sk-or-SENTINEL-9f8e7d6c5b4a-UNIQUE"
SENTINEL_WEATHER = "wx-SENTINEL-1a2b3c4d5e6f-UNIQUE"


def _force_llm_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point both keys at sentinels and make the provider call fail."""
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL_OPENROUTER)
    monkeypatch.setenv("WEATHER_API_KEY", SENTINEL_WEATHER)
    from core.config import get_settings

    get_settings.cache_clear()
    agent_module.reset_agent_cache()

    def _boom(self, *args, **kwargs):
        raise ConnectionError("simulated provider outage")

    monkeypatch.setattr(
        "langchain_classic.agents.AgentExecutor.invoke", _boom
    )


def _assert_no_sentinels(*texts: str) -> None:
    for text in texts:
        assert SENTINEL_OPENROUTER not in text
        assert SENTINEL_WEATHER not in text


def test_agent_failure_leaks_no_keys(monkeypatch, caplog):
    """Real process_chat failure path keeps sentinels out of error and logs."""
    _force_llm_failure(monkeypatch)
    with caplog.at_level(logging.INFO, logger="weathergpt"):
        with pytest.raises(RuntimeError) as exc_info:
            agent_module.process_chat(message="Weather in Mumbai?", location="Mumbai")
        logging.getLogger("weathergpt").info("probe line after failure")
    _assert_no_sentinels(str(exc_info.value), caplog.text)


@pytest.mark.asyncio
async def test_chat_route_failure_leaks_no_keys(monkeypatch, caplog):
    """502 response body and request logs carry no key material."""
    _force_llm_failure(monkeypatch)
    transport = httpx.ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="weathergpt"):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat",
                json={"message": "Weather in Mumbai?", "location": "Mumbai"},
            )
    assert response.status_code == 502
    _assert_no_sentinels(response.text, caplog.text)
