"""Chat orchestration.

``ChatService`` is the seam between the API layer and everything a chat turn
needs: it persists the user message, asks :class:`MemoryService` for the
context window, calls the configured :class:`~app.services.ai.base.AIProvider`,
and persists the assistant reply (with provider/usage metadata) so the next
turn can see it.

Both a single-shot (:meth:`send_message`) and a streaming
(:meth:`stream_message`) path are provided; they share the same persistence and
context logic so history stays consistent regardless of transport.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.models import Message, MessageRole
from app.repositories.conversations import ConversationRepository
from app.services.ai.base import AIProvider, CompletionResult, Usage
from app.services.eventbus import EventBus, EventName
from app.services.memory import MemoryService


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """Result of a completed non-streaming chat turn."""

    message: Message
    completion: CompletionResult


@dataclass(frozen=True, slots=True)
class ChatToken:
    """A streamed token delta."""

    delta: str


@dataclass(frozen=True, slots=True)
class ChatDone:
    """Terminal event of a streamed turn, carrying the persisted reply."""

    message: Message
    provider: str
    model: str | None
    finish_reason: str | None


ChatStreamEvent = ChatToken | ChatDone


class ChatService:
    """Coordinates persistence, context building and provider calls."""

    def __init__(
        self,
        conversations: ConversationRepository,
        memory: MemoryService,
        provider: AIProvider,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._conversations = conversations
        self._memory = memory
        self._provider = provider
        self._events = event_bus

    async def _emit(self, name: str, **payload: object) -> None:
        if self._events is not None:
            await self._events.emit(name, **payload)

    async def send_message(self, conversation_id: str, content: str) -> ChatTurn:
        """Persist ``content`` as a user message and return the assistant reply.

        Raises :class:`~app.core.exceptions.NotFoundError` for unknown
        conversations (the user message is only stored once the conversation is
        confirmed to exist).
        """
        await self._append_user_message(conversation_id, content)
        await self._emit(EventName.CHAT_MESSAGE_CREATED, conversation_id=conversation_id)
        context = await self._memory.build_context(conversation_id)

        completion = await self._provider.generate(context)

        assistant = await self._conversations.add_message(
            conversation_id,
            role=MessageRole.ASSISTANT,
            content=completion.content,
            meta=self._reply_meta(
                provider=completion.provider,
                model=completion.model,
                finish_reason=completion.finish_reason,
                usage=completion.usage,
            ),
            token_count=completion.usage.completion_tokens if completion.usage else None,
        )
        await self._emit(
            EventName.CHAT_RESPONSE_COMPLETED,
            conversation_id=conversation_id,
            provider=completion.provider,
        )
        return ChatTurn(message=assistant, completion=completion)

    async def stream_message(
        self, conversation_id: str, content: str
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream the assistant reply, persisting it once the stream completes.

        Yields :class:`ChatToken` for each delta and a final :class:`ChatDone`
        with the stored message. The assistant message is written only after the
        stream finishes so a partial reply is never persisted.
        """
        await self._append_user_message(conversation_id, content)
        await self._emit(EventName.CHAT_MESSAGE_CREATED, conversation_id=conversation_id)
        context = await self._memory.build_context(conversation_id)

        parts: list[str] = []
        finish_reason: str | None = None
        async for chunk in self._provider.stream(context):
            if chunk.delta:
                parts.append(chunk.delta)
                yield ChatToken(delta=chunk.delta)
            if chunk.finish_reason is not None:
                finish_reason = chunk.finish_reason

        assistant = await self._conversations.add_message(
            conversation_id,
            role=MessageRole.ASSISTANT,
            content="".join(parts),
            meta=self._reply_meta(
                provider=self._provider.name,
                model=self._provider.model,
                finish_reason=finish_reason,
                usage=None,
            ),
        )
        await self._emit(
            EventName.CHAT_RESPONSE_COMPLETED,
            conversation_id=conversation_id,
            provider=self._provider.name,
        )
        yield ChatDone(
            message=assistant,
            provider=self._provider.name,
            model=self._provider.model,
            finish_reason=finish_reason,
        )

    async def _append_user_message(self, conversation_id: str, content: str) -> Message:
        return await self._conversations.add_message(
            conversation_id, role=MessageRole.USER, content=content
        )

    @staticmethod
    def _reply_meta(
        *,
        provider: str,
        model: str | None,
        finish_reason: str | None,
        usage: Usage | None,
    ) -> dict[str, object]:
        meta: dict[str, object] = {"provider": provider, "model": model}
        if finish_reason is not None:
            meta["finish_reason"] = finish_reason
        if usage is not None:
            meta["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return meta
