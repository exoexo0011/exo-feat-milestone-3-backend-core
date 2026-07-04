"""Tool execution engine.

The engine is the single entry point for running a tool. For each invocation it:

1. resolves the tool from the registry;
2. validates arguments against the tool's parameter schema;
3. checks the permission policy (hard allow/deny);
4. enforces confirmation for sensitive tools (pausing with a pending action);
5. executes the tool, translating any failure into a :class:`ToolResult`; and
6. records the invocation in the audit trail (``AssistantAction``) when a
   repository is available.

History recording is optional: without an :class:`EventRepository` the engine
still runs tools (used by unit tests), it just does not persist an audit trail.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.models import ActionStatus
from app.repositories.events import EventRepository
from app.services.tools.base import (
    BaseTool,
    ToolContext,
    ToolError,
    ToolPermissionError,
    ToolResult,
    ToolStatus,
)
from app.services.tools.permissions import PermissionPolicy
from app.services.tools.registry import ToolRegistry

logger = logging.getLogger("exo.tools")


class ToolExecutionEngine:
    """Validates, authorises, runs and audits tool invocations."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy: PermissionPolicy,
        *,
        events: EventRepository | None = None,
    ) -> None:
        self._registry = registry
        self._policy = policy
        self._events = events

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Run tool ``name`` with ``arguments``.

        Returns a :class:`ToolResult`; expected failures (validation, denied
        permission, confirmation required, tool error) are represented as
        result statuses rather than raised, so callers get a uniform outcome.
        A missing tool still raises :class:`ToolNotFoundError`.
        """
        ctx = context or ToolContext()
        tool = self._registry.get(name)

        try:
            params = tool.params_model.model_validate(arguments)
        except ValidationError as exc:
            return ToolResult(
                tool=name,
                status=ToolStatus.FAILED,
                error=f"Invalid arguments: {_format_validation_error(exc)}",
            )

        try:
            self._policy.check(tool)
        except ToolPermissionError as exc:
            action_id = await self._record_denied(tool, arguments, ctx, exc.message)
            return ToolResult(
                tool=name, status=ToolStatus.DENIED, error=exc.message, action_id=action_id
            )

        if tool.requires_confirmation and not ctx.confirmed:
            action_id = await self._record_pending(tool, arguments, ctx)
            return ToolResult(
                tool=name,
                status=ToolStatus.CONFIRMATION_REQUIRED,
                error="This tool requires explicit confirmation before it runs.",
                action_id=action_id,
            )

        action_id = await self._record_pending(tool, arguments, ctx, confirmed=ctx.confirmed)
        return await self._run(tool, params, ctx, action_id)

    async def confirm(self, action_id: str, context: ToolContext | None = None) -> ToolResult:
        """Resume a previously ``CONFIRMATION_REQUIRED`` action and run it.

        Requires a history repository (there is nothing to resume without one).
        """
        if self._events is None:
            raise ToolError("Confirmation requires a history repository.")

        action = await self._events.get_action(action_id)
        if action.status != ActionStatus.PENDING.value:
            raise ToolError(f"Action '{action_id}' cannot be confirmed (status={action.status}).")

        tool = self._registry.get(action.tool_name)
        params = tool.params_model.model_validate(action.arguments)
        await self._events.finish_action(action_id, status=ActionStatus.CONFIRMED)
        ctx = context or ToolContext(conversation_id=action.conversation_id)
        return await self._run(tool, params, ctx, action_id)

    async def deny(self, action_id: str) -> ToolResult:
        """Reject a pending confirmation without running the tool."""
        if self._events is None:
            raise ToolError("Denial requires a history repository.")
        action = await self._events.get_action(action_id)
        await self._events.finish_action(
            action_id, status=ActionStatus.DENIED, result={"reason": "denied by user"}
        )
        return ToolResult(
            tool=action.tool_name,
            status=ToolStatus.DENIED,
            error="Denied by user.",
            action_id=action_id,
        )

    # -- internals ----------------------------------------------------------

    async def _run(
        self, tool: BaseTool[Any], params: Any, ctx: ToolContext, action_id: str | None
    ) -> ToolResult:
        try:
            output = await tool.run(params, ctx)
        except ToolError as exc:
            await self._finish(action_id, ActionStatus.FAILED, {"error": exc.message})
            return ToolResult(
                tool=tool.name, status=ToolStatus.FAILED, error=exc.message, action_id=action_id
            )
        except Exception:
            logger.exception("Unhandled error while executing tool '%s'", tool.name)
            await self._finish(action_id, ActionStatus.FAILED, {"error": "internal error"})
            return ToolResult(
                tool=tool.name,
                status=ToolStatus.FAILED,
                error="Tool execution failed due to an internal error.",
                action_id=action_id,
            )
        await self._finish(action_id, ActionStatus.COMPLETED, output)
        return ToolResult(
            tool=tool.name, status=ToolStatus.COMPLETED, output=output, action_id=action_id
        )

    async def _record_pending(
        self,
        tool: BaseTool[Any],
        arguments: dict[str, Any],
        ctx: ToolContext,
        *,
        confirmed: bool = False,
    ) -> str | None:
        if self._events is None:
            return None
        action = await self._events.log_action(
            tool_name=tool.name, arguments=arguments, conversation_id=ctx.conversation_id
        )
        if confirmed:
            await self._events.finish_action(action.id, status=ActionStatus.CONFIRMED)
        return action.id

    async def _record_denied(
        self, tool: BaseTool[Any], arguments: dict[str, Any], ctx: ToolContext, reason: str
    ) -> str | None:
        if self._events is None:
            return None
        action = await self._events.log_action(
            tool_name=tool.name, arguments=arguments, conversation_id=ctx.conversation_id
        )
        await self._events.finish_action(
            action.id, status=ActionStatus.DENIED, result={"error": reason}
        )
        return action.id

    async def _finish(
        self, action_id: str | None, status: ActionStatus, result: dict[str, Any] | None
    ) -> None:
        if self._events is None or action_id is None:
            return
        await self._events.finish_action(action_id, status=status, result=result)


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"]) or "(root)"
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)
