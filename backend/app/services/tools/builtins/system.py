"""System-facing tools: clipboard, open URL, screenshot, launch application.

Each depends on an injected backend from :mod:`app.services.tools.backends`,
keeping OS side effects out of the tool logic and enabling deterministic tests.
Side-effecting tools require confirmation; the launcher is additionally gated by
an explicit application allow-list.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, model_validator

from app.services.tools.backends import (
    AppLauncher,
    ClipboardBackend,
    Screenshotter,
    UrlOpener,
)
from app.services.tools.base import (
    BaseTool,
    Permission,
    ToolContext,
    ToolExecutionError,
    ToolPermissionError,
)
from app.services.tools.sandbox import FileSandbox

_ALLOWED_URL_SCHEMES = frozenset({"http", "https", "mailto"})


# --- clipboard --------------------------------------------------------------


class ClipboardParams(BaseModel):
    action: Literal["read", "write"] = Field(description="Whether to read or write the clipboard")
    text: str | None = Field(default=None, description="Text to write (required for 'write')")

    @model_validator(mode="after")
    def _require_text_for_write(self) -> ClipboardParams:
        if self.action == "write" and self.text is None:
            raise ValueError("'text' is required when action is 'write'")
        return self


class ClipboardTool(BaseTool[ClipboardParams]):
    name = "clipboard"
    description = "Read from or write to the system clipboard."
    permissions = frozenset({Permission.CLIPBOARD})
    params_model = ClipboardParams

    def __init__(self, backend: ClipboardBackend) -> None:
        self._backend = backend

    async def run(self, params: ClipboardParams, context: ToolContext) -> dict[str, Any]:
        if params.action == "read":
            return {"action": "read", "content": await self._backend.read()}
        # 'text' presence is guaranteed by the validator.
        assert params.text is not None
        await self._backend.write(params.text)
        return {"action": "write", "written_chars": len(params.text)}


# --- open URL ---------------------------------------------------------------


class OpenUrlParams(BaseModel):
    url: str = Field(min_length=1, description="URL to open in the default browser")


class OpenUrlTool(BaseTool[OpenUrlParams]):
    name = "open_url"
    description = "Open a URL in the user's default browser."
    permissions = frozenset({Permission.NETWORK})
    requires_confirmation = True
    params_model = OpenUrlParams

    def __init__(self, opener: UrlOpener) -> None:
        self._opener = opener

    async def run(self, params: OpenUrlParams, context: ToolContext) -> dict[str, Any]:
        parts = urlsplit(params.url)
        if parts.scheme not in _ALLOWED_URL_SCHEMES:
            raise ToolExecutionError(
                f"Unsupported URL scheme '{parts.scheme or '(none)'}'. "
                f"Allowed: {', '.join(sorted(_ALLOWED_URL_SCHEMES))}."
            )
        if parts.scheme in {"http", "https"} and not parts.netloc:
            raise ToolExecutionError("URL is missing a host.")
        await self._opener.open(params.url)
        return {"opened": params.url}


# --- screenshot -------------------------------------------------------------


class ScreenshotParams(BaseModel):
    path: str = Field(min_length=1, description="Sandbox path to save the screenshot (PNG)")


class ScreenshotTool(BaseTool[ScreenshotParams]):
    name = "screenshot"
    description = "Capture the screen and save it to a file within the sandbox."
    permissions = frozenset({Permission.SYSTEM, Permission.FILESYSTEM_WRITE})
    requires_confirmation = True
    params_model = ScreenshotParams

    def __init__(self, screenshotter: Screenshotter, sandbox: FileSandbox) -> None:
        self._screenshotter = screenshotter
        self._sandbox = sandbox

    async def run(self, params: ScreenshotParams, context: ToolContext) -> dict[str, Any]:
        destination = self._sandbox.resolve(params.path)
        await self._screenshotter.capture(destination)
        return {"path": str(destination), "captured": True}


# --- launch application -----------------------------------------------------


class LaunchAppParams(BaseModel):
    application: str = Field(min_length=1, description="Application name/path to launch")
    args: list[str] = Field(default_factory=list, description="Command-line arguments")


class LaunchApplicationTool(BaseTool[LaunchAppParams]):
    name = "launch_application"
    description = "Launch an allow-listed application."
    permissions = frozenset({Permission.PROCESS})
    requires_confirmation = True
    params_model = LaunchAppParams

    def __init__(self, launcher: AppLauncher, allowed_apps: Iterable[str]) -> None:
        self._launcher = launcher
        self._allowed_apps = frozenset(allowed_apps)

    async def run(self, params: LaunchAppParams, context: ToolContext) -> dict[str, Any]:
        if not self._allowed_apps:
            raise ToolPermissionError(
                "Launching applications is disabled: no applications are allow-listed "
                "(set EXO_TOOL_ALLOWED_APPS)."
            )
        if params.application not in self._allowed_apps:
            raise ToolPermissionError(
                f"Application '{params.application}' is not in the allow-list."
            )
        pid = await self._launcher.launch(params.application, params.args)
        return {"application": params.application, "args": params.args, "pid": pid}
