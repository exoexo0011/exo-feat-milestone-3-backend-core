"""Injectable backends for OS-facing side effects.

Tools that touch hardware or the operating system (clock, clipboard, browser,
screen capture, process launch) depend on these small abstractions rather than
calling the OS directly. This keeps the tools deterministic and unit-testable
(inject an in-memory/recording backend) while allowing real implementations in
production. All blocking OS calls are dispatched to a worker thread so the async
event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import webbrowser
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from app.services.tools.base import ToolExecutionError

# --- clock ------------------------------------------------------------------


class Clock(ABC):
    """Source of the current time (abstracted for deterministic tests)."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current timezone-aware UTC time."""


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock(Clock):
    """A clock that always returns a fixed instant (tests)."""

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


# --- clipboard --------------------------------------------------------------


class ClipboardBackend(ABC):
    @abstractmethod
    async def read(self) -> str: ...

    @abstractmethod
    async def write(self, text: str) -> None: ...


class InMemoryClipboard(ClipboardBackend):
    """A process-local clipboard. Used in tests and as a safe fallback."""

    def __init__(self, initial: str = "") -> None:
        self._value = initial

    async def read(self) -> str:
        return self._value

    async def write(self, text: str) -> None:
        self._value = text


class SystemClipboard(ClipboardBackend):
    """Best-effort OS clipboard via platform command-line utilities."""

    async def read(self) -> str:
        if sys.platform == "win32":
            return await _run_capture(["powershell", "-NoProfile", "-Command", "Get-Clipboard"])
        if sys.platform == "darwin":
            return await _run_capture(["pbpaste"])
        return await _run_capture(["xclip", "-selection", "clipboard", "-o"])

    async def write(self, text: str) -> None:
        if sys.platform == "win32":
            await _run_feed(["clip"], text)
        elif sys.platform == "darwin":
            await _run_feed(["pbcopy"], text)
        else:
            await _run_feed(["xclip", "-selection", "clipboard"], text)


# --- URL opener -------------------------------------------------------------


class UrlOpener(ABC):
    @abstractmethod
    async def open(self, url: str) -> None: ...


class WebBrowserOpener(UrlOpener):
    async def open(self, url: str) -> None:
        opened = await asyncio.to_thread(webbrowser.open, url)
        if not opened:
            raise ToolExecutionError(f"No browser available to open '{url}'.")


class RecordingUrlOpener(UrlOpener):
    """Records opened URLs instead of launching a browser (tests)."""

    def __init__(self) -> None:
        self.opened: list[str] = []

    async def open(self, url: str) -> None:
        self.opened.append(url)


# --- screenshot -------------------------------------------------------------


class Screenshotter(ABC):
    @abstractmethod
    async def capture(self, destination: Path) -> None: ...


class UnavailableScreenshotter(Screenshotter):
    """Default backend: screen capture requires a platform-specific backend.

    Kept as the safe default so the tool exists and is discoverable, but returns
    a clear error until a real capture backend is injected.
    """

    async def capture(self, destination: Path) -> None:
        raise ToolExecutionError(
            "Screen capture is not available: no screenshot backend is configured."
        )


# --- application launcher ---------------------------------------------------


class AppLauncher(ABC):
    @abstractmethod
    async def launch(self, executable: str, args: list[str]) -> int:
        """Launch ``executable`` with ``args`` and return the new process id."""


class SubprocessAppLauncher(AppLauncher):
    async def launch(self, executable: str, args: list[str]) -> int:
        def _spawn() -> int:
            process = subprocess.Popen(  # noqa: S603 - args are allow-listed by the tool
                [executable, *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return process.pid

        try:
            return await asyncio.to_thread(_spawn)
        except (OSError, ValueError) as exc:
            raise ToolExecutionError(f"Failed to launch '{executable}': {exc}") from exc


class RecordingAppLauncher(AppLauncher):
    """Records launch requests instead of spawning processes (tests)."""

    def __init__(self) -> None:
        self.launched: list[tuple[str, list[str]]] = []

    async def launch(self, executable: str, args: list[str]) -> int:
        self.launched.append((executable, args))
        return 4242


# --- helpers ----------------------------------------------------------------


async def _run_capture(command: list[str]) -> str:
    def _call() -> str:
        result = subprocess.run(  # noqa: S603 - fixed command, no shell
            command, capture_output=True, text=True, check=True
        )
        return result.stdout.rstrip("\r\n")

    try:
        return await asyncio.to_thread(_call)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ToolExecutionError(f"Clipboard read failed: {exc}") from exc


async def _run_feed(command: list[str], text: str) -> None:
    def _call() -> None:
        subprocess.run(  # noqa: S603 - fixed command, no shell
            command, input=text, text=True, check=True
        )

    try:
        await asyncio.to_thread(_call)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ToolExecutionError(f"Clipboard write failed: {exc}") from exc
