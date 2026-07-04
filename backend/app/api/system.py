"""System audit endpoints (read-only)."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.repositories.events import EventRepository
from app.schemas.events import SystemEventRead

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/events", response_model=list[SystemEventRead])
async def list_system_events(
    session: DbSession, source: str | None = None, limit: int = 100
) -> list[SystemEventRead]:
    """Return recent lifecycle audit events (newest first)."""
    events = await EventRepository(session).list_events(source=source, limit=limit)
    return [SystemEventRead.model_validate(event) for event in events]
