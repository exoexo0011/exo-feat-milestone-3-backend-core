"""Provider registry and factory.

Providers register themselves at import time via the
:meth:`ProviderFactory.register` decorator, so adding a new provider requires
no change to this module or any existing provider (Open/Closed Principle).
Selection is driven entirely by :class:`~app.config.Settings`.
"""

from __future__ import annotations

from typing import TypeVar

from app.config import Settings
from app.services.ai.base import AIProvider, ProviderNotFoundError

_ProviderT = TypeVar("_ProviderT", bound=type[AIProvider])


class ProviderFactory:
    """Registry of available providers and factory for the configured one."""

    _registry: dict[str, type[AIProvider]] = {}

    @classmethod
    def register(cls, provider_cls: _ProviderT) -> _ProviderT:
        """Class decorator that registers ``provider_cls`` under its ``name``.

        Usage::

            @ProviderFactory.register
            class MyProvider(AIProvider):
                name = "my-provider"
        """
        name = getattr(provider_cls, "name", "")
        if not name:
            raise ValueError(
                f"{provider_cls.__name__} must define a non-empty 'name' to be registered"
            )
        cls._registry[name.lower()] = provider_cls
        return provider_cls

    @classmethod
    def create(cls, settings: Settings) -> AIProvider:
        """Instantiate the provider named by ``settings.ai_provider``.

        Raises :class:`ProviderNotFoundError` if the name is not registered.
        """
        key = settings.ai_provider.strip().lower()
        provider_cls = cls._registry.get(key)
        if provider_cls is None:
            available = ", ".join(cls.available()) or "none"
            raise ProviderNotFoundError(
                f"Unknown AI provider '{settings.ai_provider}'. Registered providers: {available}"
            )
        return provider_cls.from_settings(settings)

    @classmethod
    def available(cls) -> list[str]:
        """Return the sorted list of registered provider names."""
        return sorted(cls._registry)

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Return whether a provider with ``name`` is registered."""
        return name.strip().lower() in cls._registry
