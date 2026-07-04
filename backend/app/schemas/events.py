"""System event and assistant action schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import ActionStatus


class SystemEventCreate(BaseModel):
    """Payload to record a system event."""

    level: str = Field(default="info", max_length=16)
    source: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1)
    payload: dict[str, Any] | None = None


class SystemEventRead(BaseModel):
    """System event as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    source: str
    message: str
    payload: dict[str, Any] | None
    created_at: datetime


class AssistantActionRead(BaseModel):
    """Tool invocation audit record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str | None
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    status: ActionStatus
    created_at: datetime
    completed_at: datetime | None
