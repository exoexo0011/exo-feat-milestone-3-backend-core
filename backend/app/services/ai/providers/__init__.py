"""Built-in AI providers.

Importing this package imports every built-in provider module, which triggers
their ``@ProviderFactory.register`` decorators. Adding a new built-in provider
means dropping a module here and importing it below - no existing code changes.
"""

from app.services.ai.providers.anthropic import AnthropicProvider
from app.services.ai.providers.echo import EchoProvider
from app.services.ai.providers.openai import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "EchoProvider",
    "OpenAIProvider",
]
