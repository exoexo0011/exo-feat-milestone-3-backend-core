"""User profile and preference models."""

from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class UserProfile(TimestampMixin, Base):
    """A local user of the assistant. Phase 1 uses a single default profile."""

    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    preferences: Mapped[list["Preference"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Preference(TimestampMixin, Base):
    """A single key/value preference belonging to a profile (value is JSON)."""

    __tablename__ = "preferences"
    __table_args__ = (UniqueConstraint("profile_id", "key", name="uq_preferences_profile_key"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)

    profile: Mapped[UserProfile] = relationship(back_populates="preferences")
