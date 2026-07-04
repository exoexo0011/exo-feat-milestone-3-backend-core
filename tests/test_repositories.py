"""Repository layer tests against an in-memory SQLite database."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import NotFoundError
from app.models import ActionStatus, Base, MessageRole
from app.repositories.conversations import ConversationRepository
from app.repositories.events import EventRepository
from app.repositories.users import UserRepository


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


async def test_conversation_crud(session: AsyncSession) -> None:
    repo = ConversationRepository(session)

    conversation = await repo.create("My first chat")
    assert conversation.id
    assert conversation.title == "My first chat"
    assert conversation.archived is False

    renamed = await repo.update(conversation.id, title="Renamed")
    assert renamed.title == "Renamed"

    archived = await repo.update(conversation.id, archived=True)
    assert archived.archived is True
    assert await repo.list_conversations() == []
    assert len(await repo.list_conversations(include_archived=True)) == 1

    await repo.delete(conversation.id)
    with pytest.raises(NotFoundError):
        await repo.get(conversation.id)


async def test_messages_are_ordered_and_cascade(session: AsyncSession) -> None:
    repo = ConversationRepository(session)
    conversation = await repo.create()

    await repo.add_message(conversation.id, role=MessageRole.USER, content="Hello")
    await repo.add_message(
        conversation.id,
        role=MessageRole.ASSISTANT,
        content="Hi there!",
        meta={"provider": "echo"},
        token_count=3,
    )

    messages = await repo.list_messages(conversation.id)
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[1].meta == {"provider": "echo"}

    # Deleting the conversation removes its messages (cascade).
    await repo.delete(conversation.id)
    with pytest.raises(NotFoundError):
        await repo.list_messages(conversation.id)


async def test_unknown_conversation_raises(session: AsyncSession) -> None:
    repo = ConversationRepository(session)
    with pytest.raises(NotFoundError):
        await repo.get("does-not-exist")


async def test_default_profile_and_preference_upsert(session: AsyncSession) -> None:
    repo = UserRepository(session)

    profile = await repo.get_or_create_default()
    again = await repo.get_or_create_default()
    assert profile.id == again.id  # Idempotent.

    await repo.set_preference(profile.id, "theme", "dark")
    await repo.set_preference(profile.id, "theme", "light")  # Upsert, not duplicate.
    await repo.set_preference(profile.id, "font_size", 14)

    prefs = await repo.get_preferences(profile.id)
    assert prefs == {"theme": "light", "font_size": 14}

    updated = await repo.update_profile(profile.id, display_name="Ada")
    assert updated.display_name == "Ada"


async def test_events_and_action_lifecycle(session: AsyncSession) -> None:
    repo = EventRepository(session)

    await repo.log_event(level="info", source="startup", message="Backend booted")
    events = await repo.list_events(source="startup")
    assert len(events) == 1
    assert events[0].message == "Backend booted"

    action = await repo.log_action(tool_name="calculator", arguments={"expression": "1+1"})
    assert action.status == ActionStatus.PENDING.value
    assert action.completed_at is None

    done = await repo.finish_action(action.id, status=ActionStatus.COMPLETED, result={"value": 2})
    assert done.status == ActionStatus.COMPLETED.value
    assert done.result == {"value": 2}
    assert done.completed_at is not None

    with pytest.raises(NotFoundError):
        await repo.finish_action("missing", status=ActionStatus.FAILED)
