"""Declarative base and shared model helpers."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Timezone-aware current UTC time (single source of truth for timestamps)."""
    return datetime.now(UTC)


def new_id() -> str:
    """Generate a 32-character hex identifier for primary keys."""
    return uuid4().hex


class Base(DeclarativeBase):
    """Declarative base shared by every EXO model."""


class TimestampMixin:
    """Adds created/updated audit columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
