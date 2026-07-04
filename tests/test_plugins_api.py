"""Integration tests for the plugins REST API using the real example plugin.

Points the plugin directory at the repository's ``plugins/`` folder so the
bundled ``hello_exo`` plugin is discovered and loaded by the running app.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("EXO_PLUGINS_DIR", str(PLUGINS_DIR))
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client


def test_example_plugin_is_loaded_and_enabled(client: TestClient) -> None:
    plugins = {p["name"]: p for p in client.get("/api/plugins").json()}
    assert "hello_exo" in plugins
    assert plugins["hello_exo"]["state"] == "enabled"
    assert "tool_access" in plugins["hello_exo"]["permissions"]


def test_plugin_tool_is_registered_and_executable(client: TestClient) -> None:
    tools = {t["name"] for t in client.get("/api/tools").json()}
    assert "hello_greet" in tools

    response = client.post("/api/tools/hello_greet/execute", json={"arguments": {"name": "Ada"}})
    assert response.status_code == 200
    assert "Ada" in response.json()["output"]["message"]


def test_plugin_command_execution(client: TestClient) -> None:
    commands = {(c["plugin"], c["name"]) for c in client.get("/api/plugins/commands").json()}
    assert ("hello_exo", "greet") in commands

    response = client.post(
        "/api/plugins/commands/hello_exo/greet", json={"arguments": {"name": "Sam"}}
    )
    assert response.status_code == 200
    assert "Sam" in response.json()["result"]["greeting"]


def test_disable_removes_plugin_tool(client: TestClient) -> None:
    client.post("/api/plugins/hello_exo/disable")

    detail = client.get("/api/plugins/hello_exo").json()
    assert detail["state"] == "disabled"
    tools = {t["name"] for t in client.get("/api/tools").json()}
    assert "hello_greet" not in tools

    # Re-enabling restores the tool.
    client.post("/api/plugins/hello_exo/enable")
    tools = {t["name"] for t in client.get("/api/tools").json()}
    assert "hello_greet" in tools


def test_settings_pages_and_ui_panels_exposed(client: TestClient) -> None:
    pages = client.get("/api/plugins/settings-pages").json()
    panels = client.get("/api/plugins/ui-panels").json()
    assert any(p["plugin"] == "hello_exo" for p in pages)
    assert any(p["plugin"] == "hello_exo" for p in panels)
