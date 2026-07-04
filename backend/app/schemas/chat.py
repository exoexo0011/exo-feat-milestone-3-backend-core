"""Chat request/response and WebSocket event schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.conversation import MessageRead


class ChatRequest(BaseModel):
    """Payload for sending a user message into a conversation."""

    content: str = Field(min_length=1)


class ChatUsage(BaseModel):
    """Token usage reported by the provider, when available."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    """Result of a non-streaming chat turn."""

    message: MessageRead
    provider: str
    model: str | None = None
    finish_reason: str | None = None
    usage: ChatUsage | None = None


# --- WebSocket protocol -----------------------------------------------------


class ChatSocketRequest(BaseModel):
    """A message the client sends over the chat WebSocket."""

    conversation_id: str = Field(min_length=1)
    content: str = Field(min_length=1)


class TokenEvent(BaseModel):
    """Incremental token pushed to the client during streaming."""

    type: Literal["token"] = "token"
    delta: str


class DoneEvent(BaseModel):
    """Final streaming event carrying the persisted assistant message."""

    type: Literal["done"] = "done"
    message: MessageRead
    provider: str
    model: str | None = None
    finish_reason: str | None = None


class ErrorEvent(BaseModel):
    """Error surfaced to the client without closing the socket."""

    type: Literal["error"] = "error"
    detail: str
