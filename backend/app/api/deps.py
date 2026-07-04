"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Request-scoped database session, injected into route handlers.
DbSession = Annotated[AsyncSession, Depends(get_db)]
