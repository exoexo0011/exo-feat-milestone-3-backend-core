"""Core abstractions for the AI provider layer.

This module defines the provider-agnostic message and result types plus the
:class:`AIProvider` interface every concrete provider implements. Nothing here
depends on a specific vendor SDK, which keeps the rest of the application free
of vendor lock-in: services talk to :class:`AIProvider`, never to a concrete
client.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.config import Settings
from app.core.exceptions import ExoError

# Canonical message roles understood by every provider.
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


class AIProviderError(ExoError):
    """An AI provider failed to produce a completion (upstream/transport error)."""

    status_code = 502


class ProviderNotFoundError(ExoError):
    """The configured provider name is not registered with the factory."""

    status_code = 400


class ProviderConfigurationError(ExoError):
    """A provider was selected but its required configuration is missing."""

    status_code = 500


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single conversation message handed to a provider.

    ``role`` is one of :data:`ROLE_SYSTEM`, :data:`ROLE_USER` or
    :data:`ROLE_ASSISTANT`.
    """

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting for a completion, when the provider reports it."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    """The full result of a non-streaming generation call."""

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    usage: Usage | None = None


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """An incremental piece of a streamed completion.

    ``delta`` is the text produced since the previous chunk (possibly empty).
    ``finish_reason`` is populated only on the final chunk of a stream.
    """

    delta: str
    finish_reason: str | None = None


class AIProvider(ABC):
    """Vendor-agnostic chat-completion provider.

    Concrete providers register themselves with :class:`ProviderFactory` and
    are built from application :class:`Settings` via :meth:`from_settings`.
    They must support both a single-shot :meth:`generate` call and a
    token-by-token :meth:`stream`.
    """

    #: Unique lookup name used by the factory (e.g. ``"openai"``).
    name: str

    @classmethod
    @abstractmethod
    def from_settings(cls, settings: Settings) -> AIProvider:
        """Build a provider instance from application settings."""

    @abstractmethod
    async def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        """Return a full completion for ``messages`` in a single call."""

    @abstractmethod
    def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Yield incremental :class:`StreamChunk` values as they arrive."""

    async def aclose(self) -> None:
        """Release any resources held by the provider. Default: no-op."""
        return None
