"""Tests for the pub/sub EventBus."""

from app.services.eventbus import Event, EventBus, EventName


async def test_publish_delivers_payload() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe("thing.happened", received.append)

    await bus.emit("thing.happened", value=7)

    assert len(received) == 1
    assert received[0].payload == {"value": 7}


async def test_async_and_sync_handlers() -> None:
    bus = EventBus()
    seen: list[str] = []

    async def async_handler(event: Event) -> None:
        seen.append(f"async:{event.name}")

    bus.subscribe("e", async_handler)
    bus.subscribe("e", lambda event: seen.append(f"sync:{event.name}"))

    await bus.emit("e")
    assert set(seen) == {"async:e", "sync:e"}


async def test_wildcard_receives_all_events() -> None:
    bus = EventBus()
    names: list[str] = []
    bus.subscribe(EventName.WILDCARD, lambda event: names.append(event.name))

    await bus.emit("a")
    await bus.emit("b")
    assert names == ["a", "b"]


async def test_handler_error_is_isolated() -> None:
    bus = EventBus()
    survivors: list[int] = []

    def boom(_event: Event) -> None:
        raise RuntimeError("handler exploded")

    bus.subscribe("z", boom)
    bus.subscribe("z", lambda _event: survivors.append(1))

    # Must not raise despite the failing handler.
    await bus.emit("z")
    assert survivors == [1]


async def test_unsubscribe() -> None:
    bus = EventBus()
    calls: list[int] = []
    unsubscribe = bus.subscribe("u", lambda _event: calls.append(1))
    unsubscribe()

    await bus.emit("u")
    assert calls == []
    assert bus.subscriber_count("u") == 0
