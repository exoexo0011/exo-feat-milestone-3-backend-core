"""Durable audit trail for lifecycle events.

Bridges the in-process :class:`~app.services.eventbus.EventBus` (transient) to
the ``system_events`` table so that startup/shutdown and plugin lifecycle
events are queryable after the fact. Chat and tool activity already have their
own audit records (``messages`` and ``assistant_actions``), so only
low-frequency lifecycle events are persisted here to keep the trail useful.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.events import EventRepository
from app.services.eventbus import Event, EventBus, EventName

# Only these (low-frequency, lifecycle) events are written to the audit table.
_AUDITED_EVENTS: frozenset[str] = frozenset(
    {
        EventName.SYSTEM_STARTUP.value,
        EventName.SYSTEM_SHUTDOWN.value,
        EventName.PLUGIN_LOADED.value,
        EventName.PLUGIN_ENABLED.value,
        EventName.PLUGIN_DISABLED.value,
        EventName.PLUGIN_ERROR.value,
    }
)


def register_system_audit(
    event_bus: EventBus, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Subscribe a handler that records audited events to the database.

    Handler failures are isolated by the event bus, so a transient DB error can
    never break event publishing or other subscribers.
    """

    async def _record(event: Event) -> None:
        if event.name not in _AUDITED_EVENTS:
            return
        level = "error" if event.name == EventName.PLUGIN_ERROR.value else "info"
        async with session_factory() as session:
            await EventRepository(session).log_event(
                level=level,
                source="lifecycle",
                message=event.name,
                payload=event.payload or None,
            )

    event_bus.subscribe(EventName.WILDCARD, _record)
