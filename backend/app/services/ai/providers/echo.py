"""Echo provider: a dependency-free, deterministic default.

Useful for local development, tests and CI: it needs no API key and no network
access, yet exercises the full provider contract including streaming. It simply
returns the most recent user message back to the caller.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.config import Settings
from app.services.ai.base import (
    ROLE_USER,
    AIProvider,
    ChatMessage,
    CompletionResult,
    StreamChunk,
    Usage,
)
from app.services.ai.factory import ProviderFactory

# Size of the simulated streaming chunks (characters). Chunks partition the
# text exactly, so concatenating every ``delta`` reproduces the input.
_STREAM_CHUNK_SIZE = 5


def _approx_tokens(text: str) -> int:
    """Very rough whitespace-based token estimate (echo has no tokenizer)."""
    return len(text.split())


@ProviderFactory.register
class EchoProvider(AIProvider):
    """Returns the last user message. Registered under the name ``echo``."""

    name = "echo"

    def __init__(self, *, model: str = "echo") -> None:
        self._model = model

    @property
    def model(self) -> str | None:
        return self._model

    @classmethod
    def from_settings(cls, settings: Settings) -> EchoProvider:
        return cls(model=settings.ai_model or "echo")

    @staticmethod
    def _last_user_message(messages: Sequence[ChatMessage]) -> str:
        for message in reversed(messages):
            if message.role == ROLE_USER:
                return message.content
        return messages[-1].content if messages else ""

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        text = self._last_user_message(messages)
        prompt_tokens = sum(_approx_tokens(m.content) for m in messages)
        completion_tokens = _approx_tokens(text)
        return CompletionResult(
            content=text,
            model=model or self._model,
            provider=self.name,
            finish_reason="stop",
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        text = self._last_user_message(messages)
        for start in range(0, len(text), _STREAM_CHUNK_SIZE):
            yield StreamChunk(delta=text[start : start + _STREAM_CHUNK_SIZE])
        yield StreamChunk(delta="", finish_reason="stop")
