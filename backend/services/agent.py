"""LangChain orchestration + OpenRouter connection.

Builds a tool-calling agent (Llama 3.3 via OpenRouter) bound to the
`get_current_weather` tool and exposes `process_chat()`.
"""

import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from core.config import get_settings
from tools.weather import get_climate_trends, get_current_weather, get_weather_forecast

logger = logging.getLogger(__name__)

# D-11: bound every upstream LLM call and retry exactly once, then fail loudly.
LLM_REQUEST_TIMEOUT_SECONDS = 30
LLM_MAX_ATTEMPTS = 2

SYSTEM_PROMPT = """You are WeatherGPT, a conversational assistant for weather
forecasting, alerts, and climate information, built for the Ministry of
Earth Sciences (India) and powered by IMD data.

Rules:
1. For any current-weather question, call the `get_current_weather` tool
   with the best location you have (use the `location` context if provided,
   otherwise extract it from the user's message), and quote the
   `temperature_c`, `condition`, and `alert_level` values exactly as returned
   in the tool JSON. Never invent observations.
2. For multi-day, weekend, or trip forecast questions, call the
   `get_weather_forecast` tool with the best location and requested day
   count, and quote the per-day values exactly as returned in the tool JSON.
   Never invent observations.
3. Include units (°C, %, kph, mm) and repeat the tool's short safety advisory
   when relevant.
4. End severity-sensitive replies with an IMD-style alert level on its own
   line exactly as: Alert: <Green|Yellow|Orange|Red>.
5. If the location is unknown or unmappable, ask exactly ONE clarifying
   follow-up question, then give a best-effort answer on the next turn.
   Never assume a default city such as Delhi, and never refuse outright.
6. Disclose that figures are non-IMD model data, repeat the tool `source`
   note, and surface any fallback or stale notes from the tool JSON in the
   reply.
7. Be concise and helpful.
8. For agri or climate questions, call the `get_current_weather` tool with
   the best location and, for sowing or harvest timing, also call the
   multi-day forecast tool from rule 2, then combine the live values with
   the curated advisory base, quoting the live `temperature_c` and per-day
   values exactly as returned in the tool JSON. Never invent observations.
 9. Answer any crop best-effort: never refuse for a missing or unknown crop
    — use the generic fallback advisory from the curated base and still
    ground the reply in live tool values. Rules 4 (Alert line) and 6
    (non-IMD disclosure) apply to agri replies.
 10. When tool JSON carries fallback, stale, or forecast-unavailable markers,
    answer with a still-200 graceful message: name the failed piece
    (current conditions vs forecast), state what still works (the other
    data path, cached values, or curated advice), quote the usable values
    exactly, and surface the tool note. Never convert tool-data gaps into
    refusals or 500s; the retry-once-then-fail-loudly path in process_chat
    applies to LLM outages only.
 11. For past-30-day rain/temperature trend questions, call the
    `get_climate_trends` tool with the best location and quote the
    `rain_sum_mm`, `temp_mean_c`, `wettest_day`, and `driest_day` values
    exactly as returned in the tool JSON. Disclose the 30-day window plus
    the non-IMD sourcing from the tool `source`. Never invent observations.
  """

_TOOLS = [get_current_weather, get_weather_forecast, get_climate_trends]

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "Location context: {location}\n\nUser message: {input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

_VALID_ALERTS = ("Green", "Yellow", "Orange", "Red")


def _build_llm() -> ChatOpenAI:
    """Initialize ChatOpenAI against OpenRouter (Llama 3.3)."""
    settings = get_settings()
    settings.validate_secrets(require_openrouter=True)
    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        request_timeout=LLM_REQUEST_TIMEOUT_SECONDS,
    )


@lru_cache(maxsize=1)
def _get_executor() -> AgentExecutor:
    """Build (once) the tool-calling agent executor."""
    llm = _build_llm()
    agent = create_tool_calling_agent(llm, _TOOLS, _PROMPT)
    return AgentExecutor(agent=agent, tools=_TOOLS, verbose=False, handle_parsing_errors=True)


def _derive_alert_level(reply: str, tool_output: Optional[str] = None) -> str:
    """Extract `Alert: <level>` from the reply, else fall back to tool JSON."""
    import re

    match = re.search(r"Alert:\s*(Green|Yellow|Orange|Red)", reply, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()

    if tool_output:
        try:
            data = json.loads(tool_output)
            level = str(data.get("alert_level", "Green")).capitalize()
            if level in _VALID_ALERTS:
                return level
        except (json.JSONDecodeError, AttributeError):
            pass

    lowered = reply.lower()
    if any(w in lowered for w in ("cyclone", "red alert", "extremely heavy", "flood")):
        return "Red"
    if any(w in lowered for w in ("heavy rain", "thunderstorm", "orange")):
        return "Orange"
    if any(w in lowered for w in ("rain", "drizzle", "windy", "yellow")):
        return "Yellow"
    return "Green"


def process_chat(message: str, location: Optional[str] = None) -> Dict[str, Any]:
    """Invoke the agent and return `{reply, alert_level}`.

    Args:
        message: User's natural-language query.
        location: Optional location string (may be None).

    Returns:
        Dict with keys `reply` (str) and `alert_level` (str).

    Raises:
        RuntimeError: If OPENROUTER_API_KEY is missing or the LLM call fails.
    """
    if not message or not message.strip():
        raise ValueError("message must be a non-empty string.")

    try:
        executor = _get_executor()
        result: Optional[Dict[str, Any]] = None
        last_exc: Optional[Exception] = None
        for _attempt in range(LLM_MAX_ATTEMPTS):
            try:
                result = executor.invoke(
                    {"input": message.strip(), "location": location or "unknown"}
                )
                break
            except Exception as exc:
                last_exc = exc
                logger.exception("WeatherGPT agent invocation failed (attempt logged)")
        if result is None:
            raise RuntimeError(
                f"WeatherGPT agent invocation failed: {last_exc}"
            ) from last_exc
        assert result is not None
    except RuntimeError:
        raise
    except Exception as exc:  # Wrap provider errors with actionable context.
        raise RuntimeError(f"WeatherGPT agent invocation failed: {exc}") from exc

    reply = str(result.get("output", "")).strip() or "Sorry, I could not generate a response."

    # Best-effort: recover the raw tool JSON from intermediate steps for alert fallback.
    tool_json: Optional[str] = None
    for step in result.get("intermediate_steps") or []:
        try:
            observation = step[1] if len(step) > 1 else None
            if isinstance(observation, str) and observation.strip().startswith("{"):
                tool_json = observation
        except (IndexError, TypeError):
            continue

    return {"reply": reply, "alert_level": _derive_alert_level(reply, tool_json)}


def reset_agent_cache() -> None:
    """Clear the cached executor (useful in tests after changing `.env`)."""
    _get_executor.cache_clear()
