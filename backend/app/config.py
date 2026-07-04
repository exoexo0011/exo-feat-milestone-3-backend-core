"""Central configuration for the EXO backend.

Settings are resolved from (highest precedence first):
1. Environment variables prefixed with ``EXO_``
2. A local ``.env`` file
3. Defaults defined below
"""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (immutable at runtime)."""

    model_config = SettingsConfigDict(env_prefix="EXO_", env_file=".env", extra="ignore")

    env: Literal["development", "test", "production"] = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    db_path: str = "../database/exo.db"
    log_level: str = "INFO"
    log_dir: str = "../logs"
    log_json: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- AI provider selection and generation defaults -------------------
    # ``ai_provider`` names a provider registered with ``ProviderFactory``
    # (e.g. "echo", "openai", "anthropic"). ``ai_model`` is optional; when
    # unset each provider falls back to its own sensible default model.
    ai_provider: str = "echo"
    ai_model: str | None = None
    ai_temperature: float = 0.7
    ai_max_tokens: int = 1024
    ai_request_timeout: float = 60.0

    # --- Chat pipeline ----------------------------------------------------
    # ``chat_system_prompt`` is prepended to every conversation sent to the
    # provider. ``chat_max_context_messages`` bounds how many of the most
    # recent stored messages are replayed as context (0 disables history).
    chat_system_prompt: str | None = "You are EXO, a helpful, concise AI desktop assistant."
    chat_max_context_messages: int = 20

    # --- OpenAI provider --------------------------------------------------
    # The API key accepts either ``EXO_OPENAI_API_KEY`` or the conventional
    # ``OPENAI_API_KEY`` so existing environments work unchanged.
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EXO_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openai_base_url: str = "https://api.openai.com/v1"

    # --- Anthropic provider ----------------------------------------------
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EXO_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    )
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_version: str = "2023-06-01"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
