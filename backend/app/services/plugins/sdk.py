"""Stable public SDK surface for EXO plugin authors.

Import everything you need from here::

    from app.services.plugins.sdk import (
        PluginContext, BaseTool, ToolContext, Permission, EventName,
    )

Keeping plugin imports funnelled through this module lets the internal layout
evolve without breaking third-party plugins.
"""

from app.services.eventbus import Event, EventName
from app.services.plugins.context import Command, PluginContext, SettingsPage, UiPanel
from app.services.plugins.manifest import PluginManifest, PluginPermission
from app.services.tools.base import (
    BaseTool,
    Permission,
    ToolContext,
    ToolError,
    ToolExecutionError,
    ToolResult,
    ToolStatus,
)

__all__ = [
    "BaseTool",
    "Command",
    "Event",
    "EventName",
    "Permission",
    "PluginContext",
    "PluginManifest",
    "PluginPermission",
    "SettingsPage",
    "ToolContext",
    "ToolError",
    "ToolExecutionError",
    "ToolResult",
    "ToolStatus",
    "UiPanel",
]
