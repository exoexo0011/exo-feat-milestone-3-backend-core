"""Conversation and message models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id, utcnow


class MessageRole(StrEnum):
    """Author role of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Conversation(TimestampMixin, Base):
    """A chat thread containing an ordered list of messages."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.seq",
    )


class Message(Base):
    """A single message within a conversation.

    ``meta`` stores provider- or tool-specific details (model name, tool call
    payloads, latency, ...) without requiring schema migrations.
    """

    __tablename__ = "messages"

    # ``seq`` is a monotonic autoincrement key that reflects true insertion
    # order, used for reliable message ordering (wall-clock ``created_at`` can
    # collide under coarse OS timer resolution). ``id`` remains the stable,
    # externally exposed identifier.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, default=new_id, nullable=False
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
