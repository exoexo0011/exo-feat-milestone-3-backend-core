"""Built-in tools and their discovery.

:func:`build_builtin_tools` instantiates every built-in tool with the supplied
configuration and backends and returns them ready for registration. Backends
default to their real implementations but can be overridden (dependency
injection) for tests or alternative platforms.
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.tools.backends import (
    AppLauncher,
    ClipboardBackend,
    Clock,
    Screenshotter,
    SubprocessAppLauncher,
    SystemClipboard,
    SystemClock,
    UnavailableScreenshotter,
    UrlOpener,
    WebBrowserOpener,
)
from app.services.tools.base import BaseTool
from app.services.tools.builtins.calculator import CalculatorTool
from app.services.tools.builtins.datetime_tool import CurrentTimeTool
from app.services.tools.builtins.filesystem import (
    CreateFolderTool,
    DeleteFilesTool,
    ListDirectoryTool,
    MoveFilesTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from app.services.tools.builtins.system import (
    ClipboardTool,
    LaunchApplicationTool,
    OpenUrlTool,
    ScreenshotTool,
)
from app.services.tools.sandbox import FileSandbox

__all__ = [
    "CalculatorTool",
    "ClipboardTool",
    "CreateFolderTool",
    "CurrentTimeTool",
    "DeleteFilesTool",
    "LaunchApplicationTool",
    "ListDirectoryTool",
    "MoveFilesTool",
    "OpenUrlTool",
    "ReadFileTool",
    "ScreenshotTool",
    "SearchFilesTool",
    "WriteFileTool",
    "build_builtin_tools",
]


def build_builtin_tools(
    settings: Settings,
    *,
    sandbox: FileSandbox | None = None,
    clock: Clock | None = None,
    clipboard: ClipboardBackend | None = None,
    url_opener: UrlOpener | None = None,
    screenshotter: Screenshotter | None = None,
    app_launcher: AppLauncher | None = None,
) -> list[BaseTool[Any]]:
    """Construct all built-in tools, wiring in configuration and backends."""
    sandbox = sandbox or FileSandbox.from_settings(settings)
    clock = clock or SystemClock()
    clipboard = clipboard or SystemClipboard()
    url_opener = url_opener or WebBrowserOpener()
    screenshotter = screenshotter or UnavailableScreenshotter()
    app_launcher = app_launcher or SubprocessAppLauncher()

    return [
        CalculatorTool(),
        CurrentTimeTool(clock),
        ClipboardTool(clipboard),
        OpenUrlTool(url_opener),
        ReadFileTool(sandbox),
        WriteFileTool(sandbox),
        ListDirectoryTool(sandbox),
        SearchFilesTool(sandbox),
        CreateFolderTool(sandbox),
        MoveFilesTool(sandbox),
        DeleteFilesTool(sandbox),
        ScreenshotTool(screenshotter, sandbox),
        LaunchApplicationTool(app_launcher, settings.tool_allowed_apps),
    ]
