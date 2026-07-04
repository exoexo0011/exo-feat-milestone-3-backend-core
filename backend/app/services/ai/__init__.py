"""AI provider abstraction layer.

Public surface:

* :class:`AIProvider` - the vendor-agnostic provider interface.
* :class:`ProviderFactory` - registry and factory driven by ``Settings``.
* Message/result value types: :class:`ChatMessage`, :class:`CompletionResult`,
  :class:`StreamChunk`, :class:`Usage`.
* Error types: :class:`AIProviderError`, :class:`ProviderNotFoundError`,
  :class:`ProviderConfigurationError`.

Importing this package also imports the built-in providers so they register
themselves with the factory.
"""

# Import for side effects: registers the built-in providers with the factory.
from app.services.ai import providers as _providers  # noqa: E402,F401  (ordering intentional)
from app.services.ai.base import (
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    AIProvider,
    AIProviderError,
    ChatMessage,
    CompletionResult,
    ProviderConfigurationError,
    ProviderNotFoundError,
    StreamChunk,
    Usage,
)
from app.services.ai.factory import ProviderFactory

__all__ = [
    "ROLE_ASSISTANT",
    "ROLE_SYSTEM",
    "ROLE_USER",
    "AIProvider",
    "AIProviderError",
    "ChatMessage",
    "CompletionResult",
    "ProviderConfigurationError",
    "ProviderFactory",
    "ProviderNotFoundError",
    "StreamChunk",
    "Usage",
]
