"""Health endpoint schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness/readiness payload returned by ``GET /api/health``."""

    status: Literal["ok", "degraded"]
    version: str
    env: str
    database: Literal["ok", "error"]
