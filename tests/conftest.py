"""Shared test fixtures: isolate settings and filesystem per test."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point database and logs at a temp directory and reset the settings cache."""
    monkeypatch.setenv("EXO_ENV", "test")
    monkeypatch.setenv("EXO_DB_PATH", str(tmp_path / "exo-test.db"))
    monkeypatch.setenv("EXO_LOG_DIR", str(tmp_path / "logs"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A fresh in-memory SQLite session with the full schema created."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()
