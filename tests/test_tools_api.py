"""Integration tests for the tools REST API.

Runs against the real application. A temporary filesystem sandbox root is
configured via environment so the (side-effect-free for tests) filesystem tools
can operate; clipboard/url/screenshot/launch backends are not exercised here.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("EXO_TOOL_FS_ALLOWED_ROOTS", json.dumps([tmp_path.as_posix()]))
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client


def test_list_tools(client: TestClient) -> None:
    response = client.get("/api/tools")
    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json()}
    assert len(tools) == 13
    assert "parameters" in tools["calculator"]
    assert tools["write_file"]["requires_confirmation"] is True
    assert "filesystem_write" in tools["write_file"]["permissions"]


def test_execute_calculator(client: TestClient) -> None:
    response = client.post(
        "/api/tools/calculator/execute", json={"arguments": {"expression": "2+2"}}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["output"]["result"] == 4


def test_execute_unknown_tool_returns_404(client: TestClient) -> None:
    response = client.post("/api/tools/nope/execute", json={"arguments": {}})
    assert response.status_code == 404


def test_confirmation_flow_over_rest(client: TestClient, tmp_path: Path) -> None:
    target = (tmp_path / "api.txt").as_posix()

    # Without confirmation the write is paused.
    pending = client.post(
        "/api/tools/write_file/execute",
        json={"arguments": {"path": target, "content": "written via api"}},
    ).json()
    assert pending["status"] == "confirmation_required"
    action_id = pending["action_id"]
    assert action_id
    assert not Path(target).exists()

    # Confirming runs the tool.
    confirmed = client.post(f"/api/tools/actions/{action_id}/confirm").json()
    assert confirmed["status"] == "completed"
    assert Path(target).read_text() == "written via api"


def test_execute_with_confirm_flag(client: TestClient, tmp_path: Path) -> None:
    target = (tmp_path / "direct.txt").as_posix()
    response = client.post(
        "/api/tools/write_file/execute",
        json={"arguments": {"path": target, "content": "ok"}, "confirm": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert Path(target).read_text() == "ok"


def test_history_records_invocations(client: TestClient) -> None:
    client.post("/api/tools/calculator/execute", json={"arguments": {"expression": "3+3"}})
    history = client.get("/api/tools/history").json()
    assert any(
        action["tool_name"] == "calculator" and action["status"] == "completed"
        for action in history
    )


def test_deny_flow_over_rest(client: TestClient, tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("keep me")

    pending = client.post(
        "/api/tools/delete_files/execute",
        json={"arguments": {"path": victim.as_posix()}},
    ).json()
    assert pending["status"] == "confirmation_required"

    denied = client.post(f"/api/tools/actions/{pending['action_id']}/deny").json()
    assert denied["status"] == "denied"
    assert victim.exists()
