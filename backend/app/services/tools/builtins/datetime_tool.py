"""Current-time tool.

Reports the current time via an injected :class:`Clock`, so tests are
deterministic. Supports an optional IANA timezone name (e.g. ``Europe/Paris``).
"""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field

from app.services.tools.backends import Clock, SystemClock
from app.services.tools.base import BaseTool, ToolContext, ToolExecutionError


class CurrentTimeParams(BaseModel):
    timezone: str | None = Field(
        default=None,
        description="Optional IANA timezone name (e.g. 'UTC', 'Europe/Paris'). Defaults to UTC.",
    )


class CurrentTimeTool(BaseTool[CurrentTimeParams]):
    name = "current_time"
    description = "Return the current date and time, optionally in a given IANA timezone."
    params_model = CurrentTimeParams

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()

    async def run(self, params: CurrentTimeParams, context: ToolContext) -> dict[str, Any]:
        now = self._clock.now()
        tz_name = params.timezone or "UTC"
        try:
            zone = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ToolExecutionError(f"Unknown timezone: '{tz_name}'.") from exc
        localised = now.astimezone(zone)
        return {
            "timezone": tz_name,
            "iso8601": localised.isoformat(),
            "unix": localised.timestamp(),
        }
