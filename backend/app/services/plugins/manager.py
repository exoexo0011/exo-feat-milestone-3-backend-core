"""PluginManager: discovery, loading, lifecycle and integration.

The manager ties the plugin subsystem to the rest of the app: it registers
plugin tools into the :class:`ToolRegistry`, subscribes plugin handlers on the
:class:`EventBus`, mounts plugin routers on the FastAPI app, and runs
startup/shutdown hooks. Every plugin operation is wrapped so a single plugin
failing (import error, bad hook, crashing handler) never propagates to the
application - it is recorded on the plugin's record and surfaced via the API.
"""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.services.eventbus import EventBus, EventName
from app.services.plugins import loader
from app.services.plugins.context import Command, PluginContext, SettingsPage, UiPanel
from app.services.plugins.errors import PluginError, PluginNotFoundError
from app.services.plugins.registry import PluginRecord, PluginRegistry, PluginState
from app.services.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("exo.plugins")


class PluginManager:
    """Discovers, loads and manages the lifecycle of plugins."""

    def __init__(
        self,
        plugins_dir: Path,
        *,
        tool_registry: ToolRegistry,
        event_bus: EventBus,
        exo_version: str,
        app: FastAPI | None = None,
    ) -> None:
        self._dir = plugins_dir
        self._tools = tool_registry
        self._events = event_bus
        self._version = exo_version
        self._app = app
        self.registry = PluginRegistry()
        self._commands: dict[str, Command] = {}
        self._mounted: set[str] = set()

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tools

    # -- discovery + load ---------------------------------------------------

    async def discover_and_load(self) -> None:
        """Discover every plugin, resolve order, and load compatible ones."""
        self._discover()
        for record in self._ordered_records():
            await self._load_record(record)

    def _discover(self) -> None:
        for plugin_dir in loader.discover_plugin_dirs(self._dir):
            name = plugin_dir.name
            record = PluginRecord(name=name, path=plugin_dir)
            try:
                record.manifest = loader.load_manifest(plugin_dir)
                # A directory name must match the manifest name to avoid confusion.
                if record.manifest.name != name:
                    record.state = PluginState.ERROR
                    record.error = (
                        f"Manifest name '{record.manifest.name}' does not match "
                        f"directory '{name}'."
                    )
            except PluginError as exc:
                record.state = PluginState.ERROR
                record.error = exc.message
            self.registry.add(record)

    def _ordered_records(self) -> list[PluginRecord]:
        """Topologically order discovered records by declared dependencies."""
        pending = [r for r in self.registry.all() if r.state == PluginState.DISCOVERED]
        ordered: list[PluginRecord] = []
        resolved: set[str] = set()

        while pending:
            progressed = False
            for record in list(pending):
                deps = record.manifest.dependencies if record.manifest else []
                unmet = [d for d in deps if d not in resolved]
                if not unmet:
                    ordered.append(record)
                    resolved.add(record.name)
                    pending.remove(record)
                    progressed = True
            if not progressed:
                # Remaining plugins have missing deps or form a cycle.
                for record in pending:
                    record.state = PluginState.ERROR
                    record.error = "Unresolved or circular dependencies."
                break
        return ordered

    async def _load_record(self, record: PluginRecord) -> None:
        manifest = record.manifest
        if manifest is None:
            return
        try:
            if not manifest.is_compatible_with(self._version):
                raise PluginError(
                    f"Requires EXO >= {manifest.min_exo_version}, running {self._version}."
                )
            module = loader.import_plugin_module(record.name, record.path)
            register = loader.get_register_callable(module, manifest.entry_point)
            context = PluginContext(manifest, event_bus=self._events)
            register(context)  # pure recording; no side effects yet
            record.module = module
            record.context = context
            self._mount_routers(record)
            await self._events.emit(EventName.PLUGIN_LOADED, plugin=record.name)
            if manifest.enabled_by_default:
                await self._activate(record)
            else:
                record.state = PluginState.DISABLED
        except Exception as exc:  # noqa: BLE001 - isolate any plugin failure
            record.state = PluginState.ERROR
            record.error = str(exc)
            logger.exception("Failed to load plugin '%s'", record.name)
            await self._events.emit(EventName.PLUGIN_ERROR, plugin=record.name, error=str(exc))

    # -- activation ---------------------------------------------------------

    async def _activate(self, record: PluginRecord) -> None:
        context = record.context
        if context is None:
            return
        reg = context.registration
        for tool in reg.tools:
            self._tools.register(tool)
        for command in reg.commands:
            self._commands[f"{command.plugin}.{command.name}"] = command
        for event_name, handler in reg.event_subscriptions:
            self._events.subscribe(event_name, handler)
        await self._run_hooks(reg.startup_hooks, record.name, "startup")
        record.state = PluginState.ENABLED
        record.error = None
        await self._events.emit(EventName.PLUGIN_ENABLED, plugin=record.name)

    async def _deactivate(self, record: PluginRecord) -> None:
        context = record.context
        if context is None:
            return
        reg = context.registration
        for tool in reg.tools:
            self._tools.unregister(tool.name)
        for command in reg.commands:
            self._commands.pop(f"{command.plugin}.{command.name}", None)
        self._events.unsubscribe_all(reg.event_subscriptions)
        await self._run_hooks(reg.shutdown_hooks, record.name, "shutdown")
        record.state = PluginState.DISABLED
        await self._events.emit(EventName.PLUGIN_DISABLED, plugin=record.name)

    def _mount_routers(self, record: PluginRecord) -> None:
        if self._app is None or record.context is None or record.name in self._mounted:
            return
        for router in record.context.registration.routers:
            self._app.include_router(router, prefix=f"/api/plugins/{record.name}")
        self._mounted.add(record.name)

    async def _run_hooks(self, hooks: list[Any], plugin: str, phase: str) -> None:
        for hook in hooks:
            try:
                result = hook()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Plugin '%s' %s hook failed", plugin, phase)

    # -- public control -----------------------------------------------------

    async def enable(self, name: str) -> PluginRecord:
        record = self.registry.get(name)
        if record.state == PluginState.ENABLED:
            return record
        if record.context is None:
            raise PluginError(f"Plugin '{name}' is not loaded and cannot be enabled.")
        await self._activate(record)
        return record

    async def disable(self, name: str) -> PluginRecord:
        record = self.registry.get(name)
        if record.state == PluginState.ENABLED:
            await self._deactivate(record)
        return record

    async def reload(self, name: str) -> PluginRecord:
        record = self.registry.get(name)
        if record.state == PluginState.ENABLED:
            await self._deactivate(record)
        loader.unload_module(name)
        record.module = None
        record.context = None
        self._mounted.discard(name)
        record.state = PluginState.DISCOVERED
        await self._load_record(record)
        return record

    async def shutdown(self) -> None:
        """Deactivate all enabled plugins (runs their shutdown hooks)."""
        for record in self.registry.all():
            if record.state == PluginState.ENABLED:
                await self._deactivate(record)

    # -- queries ------------------------------------------------------------

    def commands(self) -> list[Command]:
        return list(self._commands.values())

    def settings_pages(self) -> list[SettingsPage]:
        return [
            page
            for record in self._enabled()
            if record.context
            for page in record.context.registration.settings_pages
        ]

    def ui_panels(self) -> list[UiPanel]:
        return [
            panel
            for record in self._enabled()
            if record.context
            for panel in record.context.registration.ui_panels
        ]

    async def execute_command(self, plugin: str, name: str, arguments: dict[str, Any]) -> Any:
        command = self._commands.get(f"{plugin}.{name}")
        if command is None:
            raise PluginNotFoundError(f"Command '{plugin}.{name}' is not registered.")
        result = command.handler(**arguments)
        if inspect.isawaitable(result):
            return await result
        return result

    def _enabled(self) -> list[PluginRecord]:
        return [r for r in self.registry.all() if r.state == PluginState.ENABLED]
