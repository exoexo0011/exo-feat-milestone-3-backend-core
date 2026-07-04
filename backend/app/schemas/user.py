"""User profile and preference schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserProfileRead(BaseModel):
    """User profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """Partial profile update."""

    display_name: str | None = Field(default=None, min_length=1, max_length=128)


class PreferenceWrite(BaseModel):
    """Upsert payload for a single preference (value may be any JSON type)."""

    key: str = Field(min_length=1, max_length=128)
    value: Any


class PreferencesRead(BaseModel):
    """All preferences of a profile as a flat key/value mapping."""

    preferences: dict[str, Any]
