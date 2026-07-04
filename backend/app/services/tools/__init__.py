"""Tool system: interface, registry, permissions, sandbox, engine and built-ins.

Typical wiring (done once at application startup)::

    registry = build_default_registry(settings)
    policy = PermissionPolicy.from_settings(settings)
    engine = ToolExecutionEngine(registry, policy, events=event_repo)
    result = await engine.execute("calculator", {"expression": "1+1"})
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.tools.backends import (
    AppLauncher,
    ClipboardBackend,
    Clock,
    Screenshotter,
    UrlOpener,
)
from app.services.tools.base import (
    BaseTool,
    Permission,
    ToolContext,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolResult,
    ToolStatus,
    ToolValidationError,
)
from app.services.tools.builtins import build_builtin_tools
from app.services.tools.engine import ToolExecutionEngine
from app.services.tools.permissions import PermissionPolicy
from app.services.tools.registry import ToolRegistry
from app.services.tools.sandbox import FileSandbox

__all__ = [
    "BaseTool",
    "FileSandbox",
    "Permission",
    "PermissionPolicy",
    "ToolContext",
    "ToolError",
    "ToolExecutionEngine",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolPermissionError",
    "ToolRegistry",
    "ToolResult",
    "ToolStatus",
    "ToolValidationError",
    "build_default_registry",
]


def build_default_registry(
    settings: Settings,
    *,
    sandbox: FileSandbox | None = None,
    clock: Clock | None = None,
    clipboard: ClipboardBackend | None = None,
    url_opener: UrlOpener | None = None,
    screenshotter: Screenshotter | None = None,
    app_launcher: AppLauncher | None = None,
) -> ToolRegistry:
    """Build a registry populated with all built-in tools (discovery entry point)."""
    tools: list[BaseTool[Any]] = build_builtin_tools(
        settings,
        sandbox=sandbox,
        clock=clock,
        clipboard=clipboard,
        url_opener=url_opener,
        screenshotter=screenshotter,
        app_launcher=app_launcher,
    )
    return ToolRegistry(tools)
