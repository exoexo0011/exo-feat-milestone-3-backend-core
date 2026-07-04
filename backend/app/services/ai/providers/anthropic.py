"""Anthropic Messages API provider.

Talks to the ``/messages`` endpoint over HTTP (no vendor SDK required).
Anthropic differs from OpenAI in two ways handled here:

* the system prompt is a top-level ``system`` field, not a message with a
  ``system`` role, so system messages are extracted and concatenated; and
* streaming uses typed SSE events (``content_block_delta``, ``message_delta``)
  rather than OpenAI-style ``choices`` deltas.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.config import Settings
from app.services.ai.base import (
    ROLE_SYSTEM,
    ChatMessage,
    CompletionResult,
    ProviderConfigurationError,
    StreamChunk,
    Usage,
)
from app.services.ai.factory import ProviderFactory
from app.services.ai.providers._httpbase import HttpChatProvider

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


@ProviderFactory.register
class AnthropicProvider(HttpChatProvider):
    """Chat provider backed by the Anthropic REST API (name: ``anthropic``)."""

    name = "anthropic"

    def __init__(self, *, anthropic_version: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._anthropic_version = anthropic_version

    @classmethod
    def from_settings(cls, settings: Settings) -> AnthropicProvider:
        if not settings.anthropic_api_key:
            raise ProviderConfigurationError(
                "Anthropic provider requires an API key "
                "(set ANTHROPIC_API_KEY or EXO_ANTHROPIC_API_KEY)."
            )
        return cls(
            api_key=settings.anthropic_api_key,
            model=settings.ai_model or DEFAULT_MODEL,
            base_url=settings.anthropic_base_url,
            timeout=settings.ai_request_timeout,
            default_temperature=settings.ai_temperature,
            default_max_tokens=settings.ai_max_tokens,
            anthropic_version=settings.anthropic_version,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": self._anthropic_version,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _split_system(
        messages: Sequence[ChatMessage],
    ) -> tuple[str, list[dict[str, str]]]:
        """Separate system messages (top-level field) from the conversation."""
        system_parts: list[str] = []
        conversation: list[dict[str, str]] = []
        for message in messages:
            if message.role == ROLE_SYSTEM:
                system_parts.append(message.content)
            else:
                conversation.append({"role": message.role, "content": message.content})
        return "\n\n".join(system_parts), conversation

    def _payload(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        stream: bool,
    ) -> dict[str, Any]:
        system, conversation = self._split_system(messages)
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": conversation,
            "max_tokens": self._resolve_max_tokens(max_tokens),
            "temperature": self._resolve_temperature(temperature),
            "stream": stream,
        }
        if system:
            payload["system"] = system
        return payload

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
        data = await self._post_json("/messages", payload)
        blocks = data.get("content") or []
        content = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        usage_raw = data.get("usage") or {}
        input_tokens = usage_raw.get("input_tokens")
        output_tokens = usage_raw.get("output_tokens")
        total = (
            input_tokens + output_tokens
            if isinstance(input_tokens, int) and isinstance(output_tokens, int)
            else None
        )
        return CompletionResult(
            content=content,
            model=data.get("model") or payload["model"],
            provider=self.name,
            finish_reason=data.get("stop_reason"),
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total,
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
        async for data in self._iter_sse("/messages", payload):
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            if event_type == "content_block_delta":
                text = (event.get("delta") or {}).get("text") or ""
                if text:
                    yield StreamChunk(delta=text)
            elif event_type == "message_delta":
                stop_reason = (event.get("delta") or {}).get("stop_reason")
                if stop_reason:
                    yield StreamChunk(delta="", finish_reason=stop_reason)
