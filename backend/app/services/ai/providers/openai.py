"""OpenAI Chat Completions provider.

Talks to the ``/chat/completions`` endpoint over HTTP so no vendor SDK is
required. Supports both single-shot generation and token streaming (SSE).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.config import Settings
from app.services.ai.base import (
    ChatMessage,
    CompletionResult,
    ProviderConfigurationError,
    StreamChunk,
    Usage,
)
from app.services.ai.factory import ProviderFactory
from app.services.ai.providers._httpbase import HttpChatProvider

DEFAULT_MODEL = "gpt-4o-mini"


@ProviderFactory.register
class OpenAIProvider(HttpChatProvider):
    """Chat provider backed by the OpenAI REST API (name: ``openai``)."""

    name = "openai"

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAIProvider:
        if not settings.openai_api_key:
            raise ProviderConfigurationError(
                "OpenAI provider requires an API key (set OPENAI_API_KEY or EXO_OPENAI_API_KEY)."
            )
        return cls(
            api_key=settings.openai_api_key,
            model=settings.ai_model or DEFAULT_MODEL,
            base_url=settings.openai_base_url,
            timeout=settings.ai_request_timeout,
            default_temperature=settings.ai_temperature,
            default_max_tokens=settings.ai_max_tokens,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": self._resolve_model(model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self._resolve_temperature(temperature),
            "max_tokens": self._resolve_max_tokens(max_tokens),
            "stream": stream,
        }

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        payload = self._payload(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, stream=False
        )
        data = await self._post_json("/chat/completions", payload)
        choices = data.get("choices") or [{}]
        choice = choices[0]
        message = choice.get("message") or {}
        usage_raw = data.get("usage") or {}
        return CompletionResult(
            content=message.get("content") or "",
            model=data.get("model") or payload["model"],
            provider=self.name,
            finish_reason=choice.get("finish_reason"),
            usage=Usage(
                prompt_tokens=usage_raw.get("prompt_tokens"),
                completion_tokens=usage_raw.get("completion_tokens"),
                total_tokens=usage_raw.get("total_tokens"),
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
        payload = self._payload(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, stream=True
        )
        async for data in self._iter_sse("/chat/completions", payload):
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = event.get("choices") or [{}]
            choice = choices[0]
            delta = (choice.get("delta") or {}).get("content") or ""
            finish_reason = choice.get("finish_reason")
            if delta or finish_reason:
                yield StreamChunk(delta=delta, finish_reason=finish_reason)
