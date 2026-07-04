"""Conversation memory and context management.

``MemoryService`` turns stored conversation history into the bounded, ordered
list of :class:`~app.services.ai.base.ChatMessage` values a provider expects.
It owns the policy for *what* the model sees: an optional leading system prompt
plus a recency window over prior messages. Keeping this policy in one place lets
the chat pipeline evolve (summarisation, retrieval) without touching providers
or repositories.
"""

from __future__ import annotations

from app.models import MessageRole
from app.repositories.conversations import ConversationRepository
from app.services.ai.base import (
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    ChatMessage,
)

# Roles that are meaningful to send to a completion provider. Tool messages are
# excluded here; tool-call handling arrives with the tool system (Milestone 6).
_PROVIDER_ROLES = frozenset({ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT})


class MemoryService:
    """Builds provider-ready context windows from conversation history."""

    def __init__(
        self,
        conversations: ConversationRepository,
        *,
        system_prompt: str | None = None,
        max_context_messages: int = 20,
    ) -> None:
        self._conversations = conversations
        self._system_prompt = system_prompt
        self._max_context_messages = max_context_messages

    async def build_context(
        self, conversation_id: str, *, system_prompt: str | None = None
    ) -> list[ChatMessage]:
        """Return the context to send to the provider for ``conversation_id``.

        The result is ``[system?] + recent history`` in chronological order.
        ``system_prompt`` overrides the service default for this call when given.
        Raises :class:`~app.core.exceptions.NotFoundError` for unknown ids.
        """
        context: list[ChatMessage] = []

        effective_prompt = system_prompt if system_prompt is not None else self._system_prompt
        if effective_prompt:
            context.append(ChatMessage(role=ROLE_SYSTEM, content=effective_prompt))

        history = await self._conversations.list_recent_messages(
            conversation_id, limit=self._max_context_messages
        )
        for message in history:
            if message.role in _PROVIDER_ROLES:
                context.append(ChatMessage(role=message.role, content=message.content))

        return context

    @staticmethod
    def is_provider_role(role: str | MessageRole) -> bool:
        """Whether a stored message role is forwarded to the provider."""
        return str(role) in _PROVIDER_ROLES
