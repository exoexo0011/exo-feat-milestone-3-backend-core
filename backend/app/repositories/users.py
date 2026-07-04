"""Repository for user profiles and preferences."""

from typing import Any

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.models import Preference, UserProfile
from app.repositories.base import BaseRepository

DEFAULT_USERNAME = "default"
DEFAULT_DISPLAY_NAME = "EXO User"


class UserRepository(BaseRepository):
    """Profile management. Phase 1 operates on a single local default profile."""

    async def get_or_create_default(self) -> UserProfile:
        profile = await self._get_by_username(DEFAULT_USERNAME)
        if profile is None:
            profile = UserProfile(username=DEFAULT_USERNAME, display_name=DEFAULT_DISPLAY_NAME)
            self._session.add(profile)
            await self._session.commit()
            await self._session.refresh(profile)
        return profile

    async def get(self, profile_id: str) -> UserProfile:
        profile = await self._session.get(UserProfile, profile_id)
        if profile is None:
            raise NotFoundError(f"User profile '{profile_id}' not found")
        return profile

    async def update_profile(self, profile_id: str, *, display_name: str | None) -> UserProfile:
        profile = await self.get(profile_id)
        if display_name is not None:
            profile.display_name = display_name
        await self._session.commit()
        await self._session.refresh(profile)
        return profile

    async def get_preferences(self, profile_id: str) -> dict[str, Any]:
        await self.get(profile_id)  # Raises NotFoundError for unknown ids.
        stmt = select(Preference).where(Preference.profile_id == profile_id)
        result = await self._session.execute(stmt)
        return {pref.key: pref.value for pref in result.scalars().all()}

    async def set_preference(self, profile_id: str, key: str, value: Any) -> Preference:
        """Insert or update a single preference (upsert on the unique key)."""
        await self.get(profile_id)
        stmt = select(Preference).where(Preference.profile_id == profile_id, Preference.key == key)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = Preference(profile_id=profile_id, key=key, value=value)
            self._session.add(existing)
        else:
            existing.value = value
        await self._session.commit()
        await self._session.refresh(existing)
        return existing

    async def _get_by_username(self, username: str) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.username == username)
        return (await self._session.execute(stmt)).scalar_one_or_none()
