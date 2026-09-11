"""Application settings — securely loads secrets from `.env`.

SIH26068 WeatherGPT backend for the Ministry of Earth Sciences.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "WeatherGPT"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- Required secrets (loaded from .env, never hardcoded) ---
    OPENROUTER_API_KEY: str = ""
    WEATHER_API_KEY: str = ""

    # --- Demo hardening (Phase 7, D-06): env-gated, local-dev open by default ---
    CORS_ALLOW_ORIGINS: str = ""
    CHAT_THROTTLE_PER_MIN: int = 60

    # --- OpenRouter / LLM defaults ---
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    LLM_TEMPERATURE: float = 0.2

    def validate_secrets(self, *, require_openrouter: bool = True) -> None:
        """Fail fast with a clear message when a required key is missing."""
        if require_openrouter and not self.OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your `.env` file (see `.env.example`)."
            )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so `.env` is parsed only once per process."""
    return Settings()


def get_cors_allow_origins() -> list:
    """Resolve the CORS allowlist from the ``CORS_ALLOW_ORIGINS`` env var.

    Empty/unset means local-dev open (``["*"]``). When set, the value is a
    comma-separated list of exact origins — no regex, no wildcard
    passthrough — so only explicitly listed origins are reflected.
    Reads the cached settings, so tests can ``monkeypatch`` the env plus
    ``cache_clear()`` to change the outcome.
    """
    raw = get_settings().CORS_ALLOW_ORIGINS
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins:
        return ["*"]
    return origins
