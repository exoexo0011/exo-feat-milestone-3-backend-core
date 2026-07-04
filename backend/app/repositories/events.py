"""Repository for system events and assistant action audit records."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.models import ActionStatus, AssistantAction, SystemEvent, utcnow
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """Write and query the audit trail (events + tool actions)."""

    async def log_event(
        self,
        *,
        level: str,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> SystemEvent:
        event = SystemEvent(level=level, source=source, message=message, payload=payload)
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def list_events(
        self, *, source: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[SystemEvent]:
        stmt = (
            select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit).offset(offset)
        )
        if source is not None:
            stmt = stmt.where(SystemEvent.source == source)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def log_action(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        conversation_id: str | None = None,
    ) -> AssistantAction:
        """Record a tool invocation in the PENDING state."""
        action = AssistantAction(
            tool_name=tool_name, arguments=arguments, conversation_id=conversation_id
        )
        self._session.add(action)
        await self._session.commit()
        await self._session.refresh(action)
        return action

    async def get_action(self, action_id: str) -> AssistantAction:
        """Return an action by id or raise :class:`NotFoundError`."""
        action = await self._session.get(AssistantAction, action_id)
        if action is None:
            raise NotFoundError(f"Assistant action '{action_id}' not found")
        return action

    async def list_actions(
        self, *, conversation_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[AssistantAction]:
        """Return recent assistant actions, newest first."""
        stmt = (
            select(AssistantAction)
            .order_by(AssistantAction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if conversation_id is not None:
            stmt = stmt.where(AssistantAction.conversation_id == conversation_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def finish_action(
        self,
        action_id: str,
        *,
        status: ActionStatus,
        result: dict[str, Any] | None = None,
    ) -> AssistantAction:
        """Transition an action to a terminal (or confirmed) state."""
        action = await self._session.get(AssistantAction, action_id)
        if action is None:
            raise NotFoundError(f"Assistant action '{action_id}' not found")
        action.status = status.value
        action.result = result
        if status in (ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.DENIED):
            action.completed_at = utcnow()
        await self._session.commit()
        await self._session.refresh(action)
        return action
