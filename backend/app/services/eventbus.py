"""In-process publish/subscribe event bus.

Decouples producers (chat, tools, plugin lifecycle, system) from consumers
(primarily plugins). Handlers may be sync or async and are invoked with strong
error isolation: one failing subscriber never affects the publisher or other
subscribers. Subscribing to :data:`EventName.WILDCARD` receives every event.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("exo.events")


class EventName(StrEnum):
    """Canonical event names published on the bus."""

    WILDCARD = "*"

    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"

    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    PLUGIN_ERROR = "plugin.error"

    CHAT_MESSAGE_CREATED = "chat.message_created"
    CHAT_RESPONSE_COMPLETED = "chat.response_completed"

    TOOL_EXECUTED = "tool.executed"


@dataclass(frozen=True, slots=True)
class Event:
    """An event with a name and an arbitrary JSON-serialisable payload."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


# A handler receives the event and may be synchronous or asynchronous.
EventHandler = Callable[[Event], Awaitable[None] | None]


class EventBus:
    """A minimal async pub/sub bus with per-handler error isolation."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, name: str, handler: EventHandler) -> Callable[[], None]:
        """Register ``handler`` for ``name``; returns an unsubscribe callable."""
        self._handlers.setdefault(name, []).append(handler)

        def unsubscribe() -> None:
            handlers = self._handlers.get(name)
            if handlers and handler in handlers:
                handlers.remove(handler)

        return unsubscribe

    def unsubscribe_all(self, handlers: list[tuple[str, EventHandler]]) -> None:
        """Remove a batch of (name, handler) subscriptions (used on plugin unload)."""
        for name, handler in handlers:
            registered = self._handlers.get(name)
            if registered and handler in registered:
                registered.remove(handler)

    async def publish(self, event: Event) -> None:
        """Dispatch ``event`` to its subscribers and wildcard subscribers.

        Handler exceptions are logged and swallowed so a misbehaving subscriber
        cannot break the publisher or sibling subscribers.
        """
        targets = [*self._handlers.get(event.name, []), *self._handlers.get(EventName.WILDCARD, [])]
        for handler in targets:
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Event handler failed for '%s'", event.name)

    async def emit(self, name: str, **payload: Any) -> None:
        """Convenience wrapper: build and publish an :class:`Event`."""
        await self.publish(Event(name=name, payload=dict(payload)))

    def subscriber_count(self, name: str) -> int:
        return len(self._handlers.get(name, []))
