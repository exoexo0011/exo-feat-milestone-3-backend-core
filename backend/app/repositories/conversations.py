"""Repository for conversations and their messages."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.models import Conversation, Message, MessageRole, utcnow
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """CRUD operations for conversations and message history."""

    async def create(self, title: str = "New chat") -> Conversation:
        conversation = Conversation(title=title)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def get(self, conversation_id: str) -> Conversation:
        conversation = await self._session.get(Conversation, conversation_id)
        if conversation is None:
            raise NotFoundError(f"Conversation '{conversation_id}' not found")
        return conversation

    async def list_conversations(
        self, *, include_archived: bool = False, limit: int = 50, offset: int = 0
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if not include_archived:
            stmt = stmt.where(Conversation.archived.is_(False))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, conversation_id: str, *, title: str | None = None, archived: bool | None = None
    ) -> Conversation:
        conversation = await self.get(conversation_id)
        if title is not None:
            conversation.title = title
        if archived is not None:
            conversation.archived = archived
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: str) -> None:
        conversation = await self.get(conversation_id)
        await self._session.delete(conversation)
        await self._session.commit()

    async def add_message(
        self,
        conversation_id: str,
        *,
        role: MessageRole,
        content: str,
        meta: dict[str, Any] | None = None,
        token_count: int | None = None,
    ) -> Message:
        conversation = await self.get(conversation_id)
        message = Message(
            conversation_id=conversation.id,
            role=role.value,
            content=content,
            meta=meta,
            token_count=token_count,
        )
        self._session.add(message)
        # A new message bumps the conversation so it sorts to the top of the sidebar.
        conversation.updated_at = utcnow()
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def list_messages(
        self, conversation_id: str, *, limit: int = 200, offset: int = 0
    ) -> Sequence[Message]:
        await self.get(conversation_id)  # Raises NotFoundError for unknown ids.
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_recent_messages(
        self, conversation_id: str, *, limit: int = 20
    ) -> Sequence[Message]:
        """Return the most recent ``limit`` messages in chronological order.

        Unlike :meth:`list_messages` (oldest-first from an offset), this selects
        the newest messages then restores ascending order, which is what the
        chat context window needs.
        """
        await self.get(conversation_id)  # Raises NotFoundError for unknown ids.
        if limit <= 0:
            return []
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(reversed(result.scalars().all()))
