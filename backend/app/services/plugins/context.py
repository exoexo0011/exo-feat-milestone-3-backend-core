"""PluginContext: the dependency-injected API surface handed to each plugin.

A plugin's ``register(context)`` function uses this object to contribute tools,
commands, routes, settings pages, UI panels, lifecycle hooks and event
subscriptions. Every capability is gated by the plugin's declared permissions.

Registration is *pure recording*: ``register_*`` methods validate and record
intent into :class:`PluginRegistration` but do not mutate shared state. The
:class:`~app.services.plugins.manager.PluginManager` applies the registration on
enable and reverts it on disable, which keeps enable/disable symmetric and means
a ``register`` that raises midway leaves no partial state (error isolation).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter

from app.services.eventbus import EventBus, EventHandler
from app.services.plugins.errors import PluginPermissionError
from app.services.plugins.manifest import PluginManifest, PluginPermission
from app.services.tools.base import BaseTool, Permission

Hook = Callable[[], Awaitable[None] | None]
CommandHandler = Callable[..., Any]

# Maps a tool capability to the plugin permission that authorises it. Tool
# permissions with no mapping (SYSTEM, PROCESS) cannot be used by plugins.
_TOOL_PERMISSION_MAP: dict[Permission, PluginPermission] = {
    Permission.FILESYSTEM_READ: PluginPermission.FILESYSTEM_READ,
    Permission.FILESYSTEM_WRITE: PluginPermission.FILESYSTEM_WRITE,
    Permission.NETWORK: PluginPermission.NETWORK,
    Permission.CLIPBOARD: PluginPermission.CLIPBOARD,
}


@dataclass(frozen=True, slots=True)
class Command:
    plugin: str
    name: str
    description: str
    handler: CommandHandler


@dataclass(frozen=True, slots=True)
class SettingsPage:
    plugin: str
    id: str
    title: str
    schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UiPanel:
    plugin: str
    id: str
    title: str
    location: str


@dataclass
class PluginRegistration:
    """Everything a plugin registered, tracked for clean teardown."""

    tools: list[BaseTool[Any]] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    routers: list[APIRouter] = field(default_factory=list)
    settings_pages: list[SettingsPage] = field(default_factory=list)
    ui_panels: list[UiPanel] = field(default_factory=list)
    event_subscriptions: list[tuple[str, EventHandler]] = field(default_factory=list)
    startup_hooks: list[Hook] = field(default_factory=list)
    shutdown_hooks: list[Hook] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


class PluginContext:
    """Permission-scoped API passed to a plugin during registration."""

    def __init__(self, manifest: PluginManifest, *, event_bus: EventBus) -> None:
        self._manifest = manifest
        self._event_bus = event_bus
        self.registration = PluginRegistration()
        self.logger = logging.getLogger(f"exo.plugin.{manifest.name}")

    @property
    def plugin_name(self) -> str:
        return self._manifest.name

    def has_permission(self, permission: PluginPermission) -> bool:
        return self._manifest.has_permission(permission)

    def _require(self, permission: PluginPermission) -> None:
        if not self._manifest.has_permission(permission):
            raise PluginPermissionError(
                f"Plugin '{self._manifest.name}' lacks the '{permission.value}' permission."
            )

    # -- tools --------------------------------------------------------------

    def register_tool(self, tool: BaseTool[Any]) -> None:
        """Record a tool. Requires ``tool_access`` and matching capability grants."""
        self._require(PluginPermission.TOOL_ACCESS)
        for capability in tool.permissions:
            required = _TOOL_PERMISSION_MAP.get(capability)
            if required is None or not self._manifest.has_permission(required):
                raise PluginPermissionError(
                    f"Plugin '{self._manifest.name}' cannot register tool '{tool.name}': "
                    f"missing permission for capability '{capability.value}'."
                )
        self.registration.tools.append(tool)

    # -- commands -----------------------------------------------------------

    def register_command(
        self, name: str, handler: CommandHandler, *, description: str = ""
    ) -> None:
        """Record a named command callable, invokable via the plugins API."""
        self.registration.commands.append(
            Command(plugin=self._manifest.name, name=name, description=description, handler=handler)
        )

    # -- HTTP / WebSocket ---------------------------------------------------

    def register_router(self, router: APIRouter) -> None:
        """Contribute an APIRouter (mounted under /api/plugins/<name>)."""
        self.registration.routers.append(router)

    def register_websocket(self, path: str, handler: Callable[..., Awaitable[None]]) -> None:
        """Contribute a WebSocket route (mounted under /api/plugins/<name>)."""
        router = APIRouter()
        router.add_api_websocket_route(path, handler)
        self.registration.routers.append(router)

    # -- UI contributions ---------------------------------------------------

    def register_settings_page(
        self, page_id: str, title: str, schema: dict[str, Any] | None = None
    ) -> None:
        self.registration.settings_pages.append(
            SettingsPage(plugin=self._manifest.name, id=page_id, title=title, schema=schema or {})
        )

    def register_ui_panel(self, panel_id: str, title: str, location: str = "sidebar") -> None:
        self.registration.ui_panels.append(
            UiPanel(plugin=self._manifest.name, id=panel_id, title=title, location=location)
        )

    # -- lifecycle hooks ----------------------------------------------------

    def on_startup(self, hook: Hook) -> None:
        self.registration.startup_hooks.append(hook)

    def on_shutdown(self, hook: Hook) -> None:
        self.registration.shutdown_hooks.append(hook)

    # -- events -------------------------------------------------------------

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self.registration.event_subscriptions.append((event_name, handler))

    # -- runtime helpers ----------------------------------------------------

    async def notify(self, title: str, body: str) -> None:
        """Publish a notification event. Requires ``notifications``."""
        self._require(PluginPermission.NOTIFICATIONS)
        await self._event_bus.emit(
            "plugin.notification", plugin=self._manifest.name, title=title, body=body
        )

    def get_setting(self, key: str, default: Any = None) -> Any:
        self._require(PluginPermission.SETTINGS_ACCESS)
        return self.registration.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self._require(PluginPermission.SETTINGS_ACCESS)
        self.registration.settings[key] = value
