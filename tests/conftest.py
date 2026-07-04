"""Shared test fixtures: isolate settings and filesystem per test."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point database and logs at a temp directory and reset the settings cache."""
    monkeypatch.setenv("EXO_ENV", "test")
    monkeypatch.setenv("EXO_DB_PATH", str(tmp_path / "exo-test.db"))
    monkeypatch.setenv("EXO_LOG_DIR", str(tmp_path / "logs"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
