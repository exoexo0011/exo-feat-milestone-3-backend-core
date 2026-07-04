"""Tests for the lifecycle audit trail (EventBus -> system_events)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import create_app
from app.models import Base
from app.repositories.events import EventRepository
from app.services.audit import register_system_audit
from app.services.eventbus import EventBus, EventName


async def test_lifecycle_events_are_persisted() -> None:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    bus = EventBus()
    register_system_audit(bus, factory)

    await bus.emit(EventName.SYSTEM_STARTUP, version="9.9.9")
    await bus.emit(EventName.PLUGIN_ERROR, plugin="broken", error="boom")
    # A high-frequency event that must NOT be persisted to the audit table.
    await bus.emit(EventName.TOOL_EXECUTED, tool="calculator", status="completed")

    async with factory() as session:
        events = await EventRepository(session).list_events()

    messages = {e.message: e for e in events}
    assert set(messages) == {EventName.SYSTEM_STARTUP.value, EventName.PLUGIN_ERROR.value}
    assert messages[EventName.PLUGIN_ERROR.value].level == "error"
    assert messages[EventName.SYSTEM_STARTUP.value].payload == {"version": "9.9.9"}

    await engine.dispose()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_system_events_endpoint_reports_startup(client: TestClient) -> None:
    # The app lifespan emits system.startup, which the audit recorder persists.
    response = client.get("/api/system/events")
    assert response.status_code == 200
    messages = {event["message"] for event in response.json()}
    assert EventName.SYSTEM_STARTUP.value in messages


def test_system_events_filter_by_source(client: TestClient) -> None:
    response = client.get("/api/system/events", params={"source": "lifecycle"})
    assert response.status_code == 200
    assert all(event["source"] == "lifecycle" for event in response.json())
