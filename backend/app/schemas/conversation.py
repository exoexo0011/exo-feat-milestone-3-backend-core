"""Conversation and message request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import MessageRole


class ConversationCreate(BaseModel):
    """Payload to start a new conversation."""

    title: str = Field(default="New chat", min_length=1, max_length=255)


class ConversationUpdate(BaseModel):
    """Partial update: rename and/or (un)archive a conversation."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    archived: bool | None = None


class ConversationRead(BaseModel):
    """Conversation as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    archived: bool
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    """Payload to append a message to a conversation."""

    role: MessageRole
    content: str = Field(min_length=1)
    meta: dict[str, Any] | None = None


class MessageRead(BaseModel):
    """Message as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: MessageRole
    content: str
    meta: dict[str, Any] | None
    token_count: int | None
    created_at: datetime
