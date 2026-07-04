"""Integration tests for the chat REST endpoints and the chat WebSocket.

These run against the real application (default ``echo`` provider), exercising
the full stack: routing, dependencies, services, repositories and the SQLite
database created by the app lifespan.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The context manager runs the lifespan (DB init + provider creation).
    with TestClient(create_app()) as test_client:
        yield test_client


def _create_conversation(client: TestClient, title: str = "Test chat") -> str:
    response = client.post("/api/chat/conversations", json={"title": title})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_list_conversations(client: TestClient) -> None:
    conversation_id = _create_conversation(client, "First")
    listing = client.get("/api/chat/conversations")
    assert listing.status_code == 200
    ids = [c["id"] for c in listing.json()]
    assert conversation_id in ids


def test_send_message_returns_assistant_reply(client: TestClient) -> None:
    conversation_id = _create_conversation(client)

    response = client.post(
        f"/api/chat/conversations/{conversation_id}/messages",
        json={"content": "Hello there"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "echo"
    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"] == "Hello there"  # echo provider

    # History now holds the user message followed by the assistant reply.
    history = client.get(f"/api/chat/conversations/{conversation_id}/messages").json()
    assert [(m["role"], m["content"]) for m in history] == [
        ("user", "Hello there"),
        ("assistant", "Hello there"),
    ]


def test_send_message_unknown_conversation_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/chat/conversations/does-not-exist/messages",
        json={"content": "hi"},
    )
    assert response.status_code == 404


def test_send_message_validation_error(client: TestClient) -> None:
    conversation_id = _create_conversation(client)
    response = client.post(
        f"/api/chat/conversations/{conversation_id}/messages",
        json={"content": ""},
    )
    assert response.status_code == 422


def test_websocket_streams_tokens_then_done(client: TestClient) -> None:
    conversation_id = _create_conversation(client)

    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"conversation_id": conversation_id, "content": "stream me"})

        tokens: list[str] = []
        while True:
            event = ws.receive_json()
            if event["type"] == "token":
                tokens.append(event["delta"])
            elif event["type"] == "done":
                assert event["message"]["role"] == "assistant"
                assert event["message"]["content"] == "stream me"
                assert event["provider"] == "echo"
                break
            else:  # pragma: no cover - unexpected error event
                pytest.fail(f"unexpected event: {event}")

    assert "".join(tokens) == "stream me"


def test_websocket_reports_error_for_unknown_conversation(client: TestClient) -> None:
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"conversation_id": "missing", "content": "hi"})
        event = ws.receive_json()
        assert event["type"] == "error"
        assert "missing" in event["detail"]


def test_websocket_reports_error_for_invalid_payload(client: TestClient) -> None:
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"content": "no conversation id"})
        event = ws.receive_json()
        assert event["type"] == "error"
