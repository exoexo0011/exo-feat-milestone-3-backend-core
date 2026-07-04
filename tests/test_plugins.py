"""Tests for the plugin framework: loading, lifecycle, isolation, security."""

import json
from pathlib import Path

from app.services.eventbus import EventBus
from app.services.plugins.manager import PluginManager
from app.services.plugins.registry import PluginState
from app.services.tools.registry import ToolRegistry

EXO_VERSION = "0.8.0"


def make_plugin(
    root: Path,
    name: str,
    body: str,
    *,
    permissions: list[str] | None = None,
    dependencies: list[str] | None = None,
    min_exo_version: str = "0.1.0",
) -> None:
    plugin_dir = root / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "version": "1.0.0",
        "author": "test",
        "description": "test plugin",
        "permissions": permissions or [],
        "dependencies": dependencies or [],
        "min_exo_version": min_exo_version,
        "entry_point": "register",
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (plugin_dir / "__init__.py").write_text(body, encoding="utf-8")


def tool_plugin_body(tool_name: str) -> str:
    return f"""
from pydantic import BaseModel
from app.services.plugins.sdk import BaseTool, PluginContext, ToolContext


class Params(BaseModel):
    pass


class DemoTool(BaseTool[Params]):
    name = "{tool_name}"
    description = "demo"
    params_model = Params

    async def run(self, params, context):
        return {{"ok": True}}


def register(context: PluginContext) -> None:
    context.register_tool(DemoTool())
    context.register_command("ping", lambda: {{"pong": True}}, description="ping")
"""


def make_manager(root: Path) -> PluginManager:
    return PluginManager(
        root, tool_registry=ToolRegistry(), event_bus=EventBus(), exo_version=EXO_VERSION
    )


async def test_discover_and_load_enables_plugin(tmp_path: Path) -> None:
    make_plugin(tmp_path, "alpha", tool_plugin_body("alpha_tool"), permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    record = manager.registry.get("alpha")
    assert record.state is PluginState.ENABLED
    assert any(t.name == "alpha_tool" for t in manager.tool_registry)  # tool registered
    assert any(c.name == "ping" for c in manager.commands())


async def test_disable_and_enable_roundtrip(tmp_path: Path) -> None:
    make_plugin(tmp_path, "beta", tool_plugin_body("beta_tool"), permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    await manager.disable("beta")
    assert manager.registry.get("beta").state is PluginState.DISABLED
    assert not manager.tool_registry.has("beta_tool")
    assert manager.commands() == []

    await manager.enable("beta")
    assert manager.registry.get("beta").state is PluginState.ENABLED
    assert manager.tool_registry.has("beta_tool")


async def test_reload_keeps_plugin_enabled(tmp_path: Path) -> None:
    make_plugin(tmp_path, "gamma", tool_plugin_body("gamma_tool"), permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    await manager.reload("gamma")
    record = manager.registry.get("gamma")
    assert record.state is PluginState.ENABLED
    assert manager.tool_registry.has("gamma_tool")


async def test_failure_isolation(tmp_path: Path) -> None:
    make_plugin(tmp_path, "good", tool_plugin_body("good_tool"), permissions=["tool_access"])
    make_plugin(
        tmp_path,
        "broken",
        "def register(context):\n    raise RuntimeError('kaboom')\n",
    )
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    assert manager.registry.get("good").state is PluginState.ENABLED
    broken = manager.registry.get("broken")
    assert broken.state is PluginState.ERROR
    assert broken.error is not None and "kaboom" in broken.error


async def test_permission_enforcement_blocks_unauthorised_tool(tmp_path: Path) -> None:
    # Registers a tool without declaring tool_access -> load fails in isolation.
    make_plugin(tmp_path, "sneaky", tool_plugin_body("sneaky_tool"), permissions=[])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    record = manager.registry.get("sneaky")
    assert record.state is PluginState.ERROR
    assert record.error is not None and "tool_access" in record.error
    assert not manager.tool_registry.has("sneaky_tool")


async def test_capability_permission_required_for_tool(tmp_path: Path) -> None:
    body = """
from pydantic import BaseModel
from app.services.plugins.sdk import BaseTool, Permission, PluginContext, ToolContext


class Params(BaseModel):
    pass


class WriterTool(BaseTool[Params]):
    name = "writer_tool"
    description = "writes"
    permissions = frozenset({Permission.FILESYSTEM_WRITE})
    params_model = Params

    async def run(self, params, context):
        return {"ok": True}


def register(context: PluginContext) -> None:
    context.register_tool(WriterTool())
"""
    # Has tool_access but NOT filesystem_write -> must be rejected.
    make_plugin(tmp_path, "writer", body, permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    record = manager.registry.get("writer")
    assert record.state is PluginState.ERROR
    assert not manager.tool_registry.has("writer_tool")


async def test_incompatible_version_errors(tmp_path: Path) -> None:
    make_plugin(
        tmp_path,
        "future",
        tool_plugin_body("future_tool"),
        permissions=["tool_access"],
        min_exo_version="99.0.0",
    )
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    record = manager.registry.get("future")
    assert record.state is PluginState.ERROR
    assert not manager.tool_registry.has("future_tool")


async def test_missing_dependency_errors(tmp_path: Path) -> None:
    make_plugin(
        tmp_path,
        "dependent",
        tool_plugin_body("dependent_tool"),
        permissions=["tool_access"],
        dependencies=["ghost"],
    )
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    assert manager.registry.get("dependent").state is PluginState.ERROR


async def test_dependency_ordering(tmp_path: Path) -> None:
    make_plugin(tmp_path, "base", tool_plugin_body("base_tool"), permissions=["tool_access"])
    make_plugin(
        tmp_path,
        "consumer",
        tool_plugin_body("consumer_tool"),
        permissions=["tool_access"],
        dependencies=["base"],
    )
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    assert manager.registry.get("base").state is PluginState.ENABLED
    assert manager.registry.get("consumer").state is PluginState.ENABLED


async def test_execute_command(tmp_path: Path) -> None:
    make_plugin(tmp_path, "cmdplugin", tool_plugin_body("cmd_tool"), permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    result = await manager.execute_command("cmdplugin", "ping", {})
    assert result == {"pong": True}


async def test_shutdown_disables_all(tmp_path: Path) -> None:
    make_plugin(tmp_path, "svc", tool_plugin_body("svc_tool"), permissions=["tool_access"])
    manager = make_manager(tmp_path)
    await manager.discover_and_load()

    await manager.shutdown()
    assert manager.registry.get("svc").state is PluginState.DISABLED
    assert not manager.tool_registry.has("svc_tool")
