"""Unit tests for each built-in tool (no engine, injected backends)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.tools.backends import (
    FixedClock,
    InMemoryClipboard,
    RecordingAppLauncher,
    RecordingUrlOpener,
    Screenshotter,
)
from app.services.tools.base import (
    ToolContext,
    ToolExecutionError,
    ToolPermissionError,
)
from app.services.tools.builtins.calculator import CalculatorParams, CalculatorTool
from app.services.tools.builtins.datetime_tool import CurrentTimeParams, CurrentTimeTool
from app.services.tools.builtins.filesystem import (
    CreateFolderParams,
    CreateFolderTool,
    DeleteFilesParams,
    DeleteFilesTool,
    ListDirectoryParams,
    ListDirectoryTool,
    MoveFilesParams,
    MoveFilesTool,
    ReadFileParams,
    ReadFileTool,
    SearchFilesParams,
    SearchFilesTool,
    WriteFileParams,
    WriteFileTool,
)
from app.services.tools.builtins.system import (
    ClipboardParams,
    ClipboardTool,
    LaunchApplicationTool,
    LaunchAppParams,
    OpenUrlParams,
    OpenUrlTool,
    ScreenshotParams,
    ScreenshotTool,
)
from app.services.tools.sandbox import FileSandbox

CTX = ToolContext()


def _sandbox(root: Path) -> FileSandbox:
    return FileSandbox([str(root)], max_file_bytes=1024)


# --- calculator -------------------------------------------------------------


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2+3*4", 14), ("(1+2)*3", 9), ("10/4", 2.5), ("2**10", 1024), ("-5 + 2", -3)],
)
async def test_calculator_evaluates(expression: str, expected: float) -> None:
    result = await CalculatorTool().run(CalculatorParams(expression=expression), CTX)
    assert result["result"] == expected


@pytest.mark.parametrize("expression", ["1/0", "os.system('x')", "9**99999", "1 +"])
async def test_calculator_rejects_bad_input(expression: str) -> None:
    with pytest.raises(ToolExecutionError):
        await CalculatorTool().run(CalculatorParams(expression=expression), CTX)


# --- current time -----------------------------------------------------------


async def test_current_time_uses_clock_and_timezone() -> None:
    clock = FixedClock(datetime(2020, 1, 1, 12, 0, tzinfo=UTC))
    tool = CurrentTimeTool(clock)

    utc = await tool.run(CurrentTimeParams(timezone="UTC"), CTX)
    assert utc["iso8601"].startswith("2020-01-01T12:00:00")

    paris = await tool.run(CurrentTimeParams(timezone="Europe/Paris"), CTX)
    assert paris["iso8601"].startswith("2020-01-01T13:00:00")  # UTC+1 in winter


async def test_current_time_rejects_unknown_timezone() -> None:
    tool = CurrentTimeTool(FixedClock(datetime(2020, 1, 1, tzinfo=UTC)))
    with pytest.raises(ToolExecutionError):
        await tool.run(CurrentTimeParams(timezone="Mars/Olympus"), CTX)


# --- clipboard --------------------------------------------------------------


async def test_clipboard_read_and_write() -> None:
    backend = InMemoryClipboard("initial")
    tool = ClipboardTool(backend)

    read = await tool.run(ClipboardParams(action="read"), CTX)
    assert read["content"] == "initial"

    await tool.run(ClipboardParams(action="write", text="updated"), CTX)
    assert await backend.read() == "updated"


def test_clipboard_write_requires_text() -> None:
    with pytest.raises(ValueError, match="text"):
        ClipboardParams(action="write")


# --- open url ---------------------------------------------------------------


async def test_open_url_opens_valid_url() -> None:
    opener = RecordingUrlOpener()
    tool = OpenUrlTool(opener)
    await tool.run(OpenUrlParams(url="https://example.com"), CTX)
    assert opener.opened == ["https://example.com"]


@pytest.mark.parametrize("url", ["ftp://host/f", "javascript:alert(1)", "http://"])
async def test_open_url_rejects_bad_url(url: str) -> None:
    tool = OpenUrlTool(RecordingUrlOpener())
    with pytest.raises(ToolExecutionError):
        await tool.run(OpenUrlParams(url=url), CTX)


# --- filesystem -------------------------------------------------------------


async def test_write_then_read_file(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    target = (tmp_path / "note.txt").as_posix()

    await WriteFileTool(sandbox).run(WriteFileParams(path=target, content="hello"), CTX)
    read = await ReadFileTool(sandbox).run(ReadFileParams(path=target), CTX)
    assert read["content"] == "hello"


async def test_write_file_respects_size_limit(tmp_path: Path) -> None:
    sandbox = FileSandbox([str(tmp_path)], max_file_bytes=4)
    with pytest.raises(ToolExecutionError):
        await WriteFileTool(sandbox).run(
            WriteFileParams(path=(tmp_path / "big.txt").as_posix(), content="too long"), CTX
        )


async def test_list_and_search(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "b.py").write_text("2")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("3")

    listing = await ListDirectoryTool(sandbox).run(
        ListDirectoryParams(path=tmp_path.as_posix()), CTX
    )
    assert listing["count"] == 3

    found = await SearchFilesTool(sandbox).run(
        SearchFilesParams(path=tmp_path.as_posix(), pattern="*.py"), CTX
    )
    assert found["count"] == 2


async def test_create_move_delete(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)

    folder = (tmp_path / "docs").as_posix()
    await CreateFolderTool(sandbox).run(CreateFolderParams(path=folder), CTX)
    assert (tmp_path / "docs").is_dir()

    (tmp_path / "docs" / "x.txt").write_text("data")
    await MoveFilesTool(sandbox).run(
        MoveFilesParams(
            source=(tmp_path / "docs" / "x.txt").as_posix(),
            destination=(tmp_path / "docs" / "y.txt").as_posix(),
        ),
        CTX,
    )
    assert not (tmp_path / "docs" / "x.txt").exists()
    assert (tmp_path / "docs" / "y.txt").exists()

    await DeleteFilesTool(sandbox).run(
        DeleteFilesParams(path=(tmp_path / "docs").as_posix(), recursive=True), CTX
    )
    assert not (tmp_path / "docs").exists()


async def test_delete_nonempty_without_recursive_fails(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "f.txt").write_text("x")
    with pytest.raises(ToolExecutionError):
        await DeleteFilesTool(sandbox).run(DeleteFilesParams(path=(tmp_path / "d").as_posix()), CTX)


async def test_sandbox_blocks_traversal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("nope")
    sandbox = _sandbox(root)
    with pytest.raises(ToolPermissionError):
        await ReadFileTool(sandbox).run(ReadFileParams(path=outside.as_posix()), CTX)


def test_sandbox_disabled_without_roots() -> None:
    with pytest.raises(ToolPermissionError):
        FileSandbox([]).resolve("/anything")


# --- screenshot -------------------------------------------------------------


class _FakeScreenshotter(Screenshotter):
    async def capture(self, destination: Path) -> None:
        destination.write_bytes(b"PNG")


async def test_screenshot_saves_file(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path)
    target = (tmp_path / "shot.png").as_posix()
    result = await ScreenshotTool(_FakeScreenshotter(), sandbox).run(
        ScreenshotParams(path=target), CTX
    )
    assert result["captured"] is True
    assert (tmp_path / "shot.png").read_bytes() == b"PNG"


# --- launch application -----------------------------------------------------


async def test_launch_allowed_application() -> None:
    launcher = RecordingAppLauncher()
    tool = LaunchApplicationTool(launcher, ["notepad"])
    result = await tool.run(LaunchAppParams(application="notepad", args=["a.txt"]), CTX)
    assert result["pid"] == 4242
    assert launcher.launched == [("notepad", ["a.txt"])]


async def test_launch_rejects_unlisted_application() -> None:
    tool = LaunchApplicationTool(RecordingAppLauncher(), ["notepad"])
    with pytest.raises(ToolPermissionError):
        await tool.run(LaunchAppParams(application="rm"), CTX)


async def test_launch_denied_when_no_allowlist() -> None:
    tool = LaunchApplicationTool(RecordingAppLauncher(), [])
    with pytest.raises(ToolPermissionError):
        await tool.run(LaunchAppParams(application="notepad"), CTX)
