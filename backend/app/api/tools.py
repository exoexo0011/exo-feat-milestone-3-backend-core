"""REST endpoints for listing, executing and auditing tools.

Security note: these endpoints expose local capabilities (filesystem, process
launch, ...). They are unauthenticated like the rest of the local-first backend
and rely on the permission policy, filesystem sandbox and confirmation flow for
safety. Add authentication before exposing the backend beyond localhost.
"""

from fastapi import APIRouter

from app.api.deps import DbSession, ToolEngineDep, ToolRegistryDep
from app.repositories.events import EventRepository
from app.schemas.events import AssistantActionRead
from app.schemas.tools import ToolExecuteRequest, ToolResultResponse, ToolSpec
from app.services.tools.base import ToolContext

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolSpec])
async def list_tools(registry: ToolRegistryDep) -> list[ToolSpec]:
    """List every registered tool and its parameter schema."""
    return [ToolSpec.model_validate(spec) for spec in registry.specs()]


@router.post("/{name}/execute", response_model=ToolResultResponse)
async def execute_tool(
    name: str, payload: ToolExecuteRequest, engine: ToolEngineDep
) -> ToolResultResponse:
    """Execute a tool. Tools requiring confirmation return ``confirmation_required``
    unless ``confirm`` is true."""
    context = ToolContext(confirmed=payload.confirm, conversation_id=payload.conversation_id)
    result = await engine.execute(name, payload.arguments, context)
    return ToolResultResponse.from_result(result)


@router.post("/actions/{action_id}/confirm", response_model=ToolResultResponse)
async def confirm_action(action_id: str, engine: ToolEngineDep) -> ToolResultResponse:
    """Confirm and run a previously pending tool action."""
    result = await engine.confirm(action_id)
    return ToolResultResponse.from_result(result)


@router.post("/actions/{action_id}/deny", response_model=ToolResultResponse)
async def deny_action(action_id: str, engine: ToolEngineDep) -> ToolResultResponse:
    """Deny a pending tool action without running it."""
    result = await engine.deny(action_id)
    return ToolResultResponse.from_result(result)


@router.get("/history", response_model=list[AssistantActionRead])
async def tool_history(session: DbSession, limit: int = 50) -> list[AssistantActionRead]:
    """Return recent tool invocations from the audit trail (newest first)."""
    actions = await EventRepository(session).list_actions(limit=limit)
    return [AssistantActionRead.model_validate(action) for action in actions]
