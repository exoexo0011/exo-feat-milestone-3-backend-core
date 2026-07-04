"""Tests for the tool framework: registry, permissions, engine and history."""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import ActionStatus
from app.repositories.events import EventRepository
from app.services.tools import (
    Permission,
    PermissionPolicy,
    ToolContext,
    ToolExecutionEngine,
    ToolRegistry,
    ToolStatus,
    build_default_registry,
)
from app.services.tools.backends import InMemoryClipboard, RecordingUrlOpener
from app.services.tools.base import ToolNotFoundError
from app.services.tools.builtins.calculator import CalculatorTool


def _settings(root: Path) -> Settings:
    return Settings(tool_fs_allowed_roots=[root.as_posix()], tool_allowed_apps=["notepad"])


def _registry(root: Path) -> ToolRegistry:
    # Inject in-memory backends so no OS side effects occur.
    return build_default_registry(
        _settings(root), clipboard=InMemoryClipboard(), url_opener=RecordingUrlOpener()
    )


def _engine(
    root: Path, session: AsyncSession, policy: PermissionPolicy | None = None
) -> ToolExecutionEngine:
    return ToolExecutionEngine(
        _registry(root), policy or PermissionPolicy(), events=EventRepository(session)
    )


# --- registry ---------------------------------------------------------------


def test_registry_rejects_duplicates() -> None:
    registry = ToolRegistry([CalculatorTool()])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(CalculatorTool())


def test_default_registry_contains_all_builtins(tmp_path: Path) -> None:
    names = set(_registry(tmp_path).names())
    assert names == {
        "calculator",
        "current_time",
        "clipboard",
        "open_url",
        "read_file",
        "write_file",
        "list_directory",
        "search_files",
        "create_folder",
        "move_files",
        "delete_files",
        "screenshot",
        "launch_application",
    }


# --- permissions ------------------------------------------------------------


def test_permission_policy_from_settings_validates_names(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown permission"):
        PermissionPolicy.from_settings(Settings(tool_denied_permissions=["not_a_permission"]))


# --- engine -----------------------------------------------------------------


async def test_engine_runs_calculator_and_records_history(
    tmp_path: Path, db_session: AsyncSession
) -> None:
    engine = _engine(tmp_path, db_session)
    result = await engine.execute("calculator", {"expression": "6*7"})

    assert result.ok
    assert result.output == {"expression": "6*7", "result": 42}
    assert result.action_id is not None

    action = await EventRepository(db_session).get_action(result.action_id)
    assert action.status == ActionStatus.COMPLETED.value
    assert action.result == {"expression": "6*7", "result": 42}


async def test_engine_validation_error_is_failed(tmp_path: Path, db_session: AsyncSession) -> None:
    engine = _engine(tmp_path, db_session)
    result = await engine.execute("calculator", {"not_expression": 1})
    assert result.status is ToolStatus.FAILED
    assert result.error is not None and "Invalid arguments" in result.error


async def test_engine_unknown_tool_raises(tmp_path: Path, db_session: AsyncSession) -> None:
    engine = _engine(tmp_path, db_session)
    with pytest.raises(ToolNotFoundError):
        await engine.execute("nonexistent", {})


async def test_engine_denies_tool_with_denied_permission(
    tmp_path: Path, db_session: AsyncSession
) -> None:
    policy = PermissionPolicy(denied=[Permission.FILESYSTEM_WRITE])
    engine = _engine(tmp_path, db_session, policy)
    result = await engine.execute(
        "write_file",
        {"path": (tmp_path / "x.txt").as_posix(), "content": "hi"},
        ToolContext(confirmed=True),
    )
    assert result.status is ToolStatus.DENIED
    action = await EventRepository(db_session).get_action(result.action_id or "")
    assert action.status == ActionStatus.DENIED.value


async def test_engine_confirmation_flow(tmp_path: Path, db_session: AsyncSession) -> None:
    engine = _engine(tmp_path, db_session)
    target = (tmp_path / "confirmed.txt").as_posix()

    # First call: no confirmation -> paused with a pending action.
    pending = await engine.execute("write_file", {"path": target, "content": "data"})
    assert pending.status is ToolStatus.CONFIRMATION_REQUIRED
    assert pending.action_id is not None
    assert not Path(target).exists()

    action = await EventRepository(db_session).get_action(pending.action_id)
    assert action.status == ActionStatus.PENDING.value

    # Confirm -> runs and completes.
    done = await engine.confirm(pending.action_id)
    assert done.ok
    assert Path(target).read_text() == "data"
    action = await EventRepository(db_session).get_action(pending.action_id)
    assert action.status == ActionStatus.COMPLETED.value


async def test_engine_deny_flow(tmp_path: Path, db_session: AsyncSession) -> None:
    engine = _engine(tmp_path, db_session)
    target = tmp_path / "keep.txt"
    target.write_text("original")

    pending = await engine.execute("delete_files", {"path": target.as_posix()})
    assert pending.status is ToolStatus.CONFIRMATION_REQUIRED

    denied = await engine.deny(pending.action_id or "")
    assert denied.status is ToolStatus.DENIED
    assert target.exists()  # not deleted


async def test_engine_without_history_still_runs(tmp_path: Path) -> None:
    engine = ToolExecutionEngine(_registry(tmp_path), PermissionPolicy())
    result = await engine.execute("calculator", {"expression": "1+1"})
    assert result.ok
    assert result.action_id is None  # no history repository
