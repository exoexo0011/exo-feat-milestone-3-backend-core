"""Repository base class."""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Common base for repositories bound to a request-scoped ``AsyncSession``.

    Repositories own their transactions: every public mutating method commits
    before returning, so callers always observe persisted state.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
