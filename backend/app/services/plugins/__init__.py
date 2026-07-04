"""Plugin subsystem: manifest, context, registry, loader and manager.

Wiring (done once at startup)::

    manager = PluginManager(dir, tool_registry=..., event_bus=..., exo_version=..., app=app)
    await manager.discover_and_load()
    ...
    await manager.shutdown()

Plugin authors import from :mod:`app.services.plugins.sdk`.
"""

from app.services.plugins.context import (
    Command,
    PluginContext,
    PluginRegistration,
    SettingsPage,
    UiPanel,
)
from app.services.plugins.errors import (
    PluginDependencyError,
    PluginError,
    PluginLoadError,
    PluginManifestError,
    PluginNotFoundError,
    PluginPermissionError,
    PluginVersionError,
)
from app.services.plugins.manager import PluginManager
from app.services.plugins.manifest import PluginManifest, PluginPermission
from app.services.plugins.registry import PluginRecord, PluginRegistry, PluginState

__all__ = [
    "Command",
    "PluginContext",
    "PluginDependencyError",
    "PluginError",
    "PluginLoadError",
    "PluginManager",
    "PluginManifest",
    "PluginManifestError",
    "PluginNotFoundError",
    "PluginPermission",
    "PluginPermissionError",
    "PluginRecord",
    "PluginRegistration",
    "PluginRegistry",
    "PluginState",
    "PluginVersionError",
    "SettingsPage",
    "UiPanel",
]
