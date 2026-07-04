"""Unit tests for the AI provider layer.

Network providers (OpenAI, Anthropic) are exercised against an in-process
``httpx.MockTransport`` so no real API calls are made.
"""

import json

import httpx
import pytest

from app.config import Settings
from app.services.ai import (
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    AIProviderError,
    ChatMessage,
    ProviderConfigurationError,
    ProviderFactory,
    ProviderNotFoundError,
)
from app.services.ai.providers.anthropic import AnthropicProvider
from app.services.ai.providers.echo import EchoProvider
from app.services.ai.providers.openai import OpenAIProvider


def _messages() -> list[ChatMessage]:
    return [
        ChatMessage(role=ROLE_SYSTEM, content="You are helpful."),
        ChatMessage(role=ROLE_USER, content="Hello there, EXO!"),
    ]


# --- Factory / registration -------------------------------------------------


def test_builtin_providers_are_registered() -> None:
    available = ProviderFactory.available()
    assert {"echo", "openai", "anthropic"} <= set(available)


def test_factory_creates_echo_from_settings() -> None:
    provider = ProviderFactory.create(Settings(ai_provider="echo"))
    assert isinstance(provider, EchoProvider)


def test_factory_unknown_provider_raises() -> None:
    with pytest.raises(ProviderNotFoundError):
        ProviderFactory.create(Settings(ai_provider="does-not-exist"))


def test_factory_openai_without_key_raises_configuration_error() -> None:
    with pytest.raises(ProviderConfigurationError):
        ProviderFactory.create(Settings(ai_provider="openai", openai_api_key=None))


def test_register_requires_name() -> None:
    with pytest.raises(ValueError, match="non-empty 'name'"):

        @ProviderFactory.register  # type: ignore[type-var]
        class _Nameless:  # noqa: N801
            name = ""


# --- Echo provider ----------------------------------------------------------


async def test_echo_generate_returns_last_user_message() -> None:
    provider = EchoProvider()
    result = await provider.generate(_messages())
    assert result.content == "Hello there, EXO!"
    assert result.provider == "echo"
    assert result.finish_reason == "stop"
    assert result.usage is not None
    assert result.usage.completion_tokens == 3


async def test_echo_stream_reconstructs_content() -> None:
    provider = EchoProvider()
    chunks = [chunk async for chunk in provider.stream(_messages())]
    text = "".join(c.delta for c in chunks)
    assert text == "Hello there, EXO!"
    assert chunks[-1].finish_reason == "stop"


# --- OpenAI provider --------------------------------------------------------


def _openai_provider(handler: httpx.MockTransport) -> OpenAIProvider:
    return OpenAIProvider(
        api_key="test-key",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        timeout=5.0,
        default_temperature=0.7,
        default_max_tokens=64,
        client=httpx.AsyncClient(transport=handler),
    )


async def test_openai_generate_parses_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        body = json.loads(request.content)
        assert body["stream"] is False
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(
            200,
            json={
                "model": "gpt-4o-mini",
                "choices": [{"message": {"content": "Hi!"}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 1,
                    "total_tokens": 6,
                },
            },
        )

    provider = _openai_provider(httpx.MockTransport(handler))
    result = await provider.generate(_messages())
    assert result.content == "Hi!"
    assert result.finish_reason == "stop"
    assert result.usage is not None
    assert result.usage.total_tokens == 6
    await provider.aclose()


async def test_openai_stream_parses_deltas() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["stream"] is True
        sse = (
            'data: {"choices":[{"delta":{"content":"He"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n'
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, content=sse.encode())

    provider = _openai_provider(httpx.MockTransport(handler))
    chunks = [chunk async for chunk in provider.stream(_messages())]
    assert "".join(c.delta for c in chunks) == "Hello"
    assert chunks[-1].finish_reason == "stop"
    await provider.aclose()


async def test_openai_error_status_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid key"})

    provider = _openai_provider(httpx.MockTransport(handler))
    with pytest.raises(AIProviderError):
        await provider.generate(_messages())
    await provider.aclose()


# --- Anthropic provider -----------------------------------------------------


def _anthropic_provider(handler: httpx.MockTransport) -> AnthropicProvider:
    return AnthropicProvider(
        api_key="test-key",
        model="claude-3-5-sonnet-20241022",
        base_url="https://api.anthropic.com/v1",
        timeout=5.0,
        default_temperature=0.7,
        default_max_tokens=64,
        anthropic_version="2023-06-01",
        client=httpx.AsyncClient(transport=handler),
    )


async def test_anthropic_generate_extracts_system_and_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/messages")
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        body = json.loads(request.content)
        # System message is lifted out of the messages array.
        assert body["system"] == "You are helpful."
        assert [m["role"] for m in body["messages"]] == ["user"]
        return httpx.Response(
            200,
            json={
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "Hello!"}],
                "usage": {"input_tokens": 10, "output_tokens": 2},
            },
        )

    provider = _anthropic_provider(httpx.MockTransport(handler))
    result = await provider.generate(_messages())
    assert result.content == "Hello!"
    assert result.finish_reason == "end_turn"
    assert result.usage is not None
    assert result.usage.total_tokens == 12
    await provider.aclose()


async def test_anthropic_stream_parses_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        sse = (
            "event: content_block_delta\n"
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}\n\n'
            "event: content_block_delta\n"
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" EXO"}}\n\n'
            "event: message_delta\n"
            'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\n\n'
        )
        return httpx.Response(200, content=sse.encode())

    provider = _anthropic_provider(httpx.MockTransport(handler))
    chunks = [chunk async for chunk in provider.stream([ChatMessage(role=ROLE_USER, content="hi")])]
    assert "".join(c.delta for c in chunks) == "Hi EXO"
    assert chunks[-1].finish_reason == "end_turn"
    await provider.aclose()


async def test_anthropic_multiturn_roles_preserved() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    provider = _anthropic_provider(httpx.MockTransport(handler))
    await provider.generate(
        [
            ChatMessage(role=ROLE_USER, content="first"),
            ChatMessage(role=ROLE_ASSISTANT, content="reply"),
            ChatMessage(role=ROLE_USER, content="second"),
        ]
    )
    body = captured["body"]
    assert isinstance(body, dict)
    assert [m["role"] for m in body["messages"]] == ["user", "assistant", "user"]
    assert "system" not in body
    await provider.aclose()
