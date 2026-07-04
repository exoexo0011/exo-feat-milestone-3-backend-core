"""Health endpoint: liveness plus a database round-trip check."""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import DbSession
from app.config import get_settings
from app.schemas.health import HealthResponse

logger = logging.getLogger("exo.health")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: DbSession) -> HealthResponse:
    """Report service status; degraded when the database is unreachable."""
    database_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        database_ok = False
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        version=__version__,
        env=get_settings().env,
        database="ok" if database_ok else "error",
    )
