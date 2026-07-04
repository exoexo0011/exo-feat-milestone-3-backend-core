"""Unit and integration tests for the Milestone 5 chat pipeline."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import MessageRole
from app.repositories.conversations import ConversationRepository
from app.services.ai.providers.echo import EchoProvider
from app.services.chat import ChatDone, ChatService, ChatToken
from app.services.memory import MemoryService


def _chat_service(
    session: AsyncSession, *, system_prompt: str | None, window: int = 20
) -> ChatService:
    conversations = ConversationRepository(session)
    memory = MemoryService(conversations, system_prompt=system_prompt, max_context_messages=window)
    return ChatService(conversations, memory, EchoProvider())


# --- MemoryService ----------------------------------------------------------


async def test_memory_prepends_system_prompt_and_orders_history(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    await repo.add_message(conversation.id, role=MessageRole.USER, content="one")
    await repo.add_message(conversation.id, role=MessageRole.ASSISTANT, content="two")

    memory = MemoryService(repo, system_prompt="SYS", max_context_messages=20)
    context = await memory.build_context(conversation.id)

    assert [(m.role, m.content) for m in context] == [
        ("system", "SYS"),
        ("user", "one"),
        ("assistant", "two"),
    ]


async def test_memory_windows_to_recent_messages(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    for i in range(5):
        await repo.add_message(conversation.id, role=MessageRole.USER, content=f"m{i}")

    memory = MemoryService(repo, system_prompt=None, max_context_messages=2)
    context = await memory.build_context(conversation.id)

    # Only the two most recent messages, in chronological order, no system prompt.
    assert [m.content for m in context] == ["m3", "m4"]


async def test_memory_skips_tool_messages(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    await repo.add_message(conversation.id, role=MessageRole.USER, content="hi")
    await repo.add_message(conversation.id, role=MessageRole.TOOL, content="tool-output")

    memory = MemoryService(repo, system_prompt=None)
    context = await memory.build_context(conversation.id)

    assert [m.role for m in context] == ["user"]


# --- ChatService ------------------------------------------------------------


async def test_send_message_persists_user_and_assistant(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    service = _chat_service(db_session, system_prompt="SYS")

    turn = await service.send_message(conversation.id, "Hello EXO")

    # Echo returns the latest user message.
    assert turn.message.content == "Hello EXO"
    assert turn.message.role == MessageRole.ASSISTANT.value
    assert turn.completion.provider == "echo"
    assert turn.message.meta is not None
    assert turn.message.meta["provider"] == "echo"

    history = await repo.list_messages(conversation.id)
    assert [(m.role, m.content) for m in history] == [
        ("user", "Hello EXO"),
        ("assistant", "Hello EXO"),
    ]


async def test_send_message_unknown_conversation_raises(db_session: AsyncSession) -> None:
    service = _chat_service(db_session, system_prompt=None)
    with pytest.raises(NotFoundError):
        await service.send_message("missing", "hi")


async def test_stream_message_yields_tokens_then_done(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    service = _chat_service(db_session, system_prompt=None)

    events = [event async for event in service.stream_message(conversation.id, "streaming!")]

    tokens = [e for e in events if isinstance(e, ChatToken)]
    done = [e for e in events if isinstance(e, ChatDone)]
    assert len(done) == 1
    assert "".join(t.delta for t in tokens) == "streaming!"
    assert done[0].finish_reason == "stop"
    assert done[0].message.content == "streaming!"

    # The assistant reply is persisted exactly once, after streaming completes.
    history = await repo.list_messages(conversation.id)
    assert [(m.role, m.content) for m in history] == [
        ("user", "streaming!"),
        ("assistant", "streaming!"),
    ]
