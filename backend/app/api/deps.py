"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.conversations import ConversationRepository
from app.repositories.events import EventRepository
from app.services.ai.base import AIProvider
from app.services.chat import ChatService
from app.services.eventbus import EventBus
from app.services.memory import MemoryService
from app.services.plugins import PluginManager
from app.services.tools import PermissionPolicy, ToolExecutionEngine, ToolRegistry

# Request-scoped database session, injected into route handlers.
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_ai_provider(request: Request) -> AIProvider:
    """Return the process-wide provider created during application startup."""
    provider: AIProvider = request.app.state.ai_provider
    return provider


AiProvider = Annotated[AIProvider, Depends(get_ai_provider)]


def get_event_bus(request: Request) -> EventBus:
    """Return the process-wide event bus."""
    bus: EventBus = request.app.state.event_bus
    return bus


def build_chat_service(
    session: AsyncSession,
    provider: AIProvider,
    settings: Settings,
    event_bus: EventBus | None = None,
) -> ChatService:
    """Assemble a :class:`ChatService` and its collaborators for one request.

    Shared by the REST dependency and the WebSocket handler so both transports
    build the pipeline identically.
    """
    conversations = ConversationRepository(session)
    memory = MemoryService(
        conversations,
        system_prompt=settings.chat_system_prompt,
        max_context_messages=settings.chat_max_context_messages,
    )
    return ChatService(conversations, memory, provider, event_bus=event_bus)


def get_chat_service(session: DbSession, provider: AiProvider, request: Request) -> ChatService:
    """FastAPI dependency providing a fully wired chat service."""
    return build_chat_service(session, provider, get_settings(), get_event_bus(request))


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_plugin_manager(request: Request) -> PluginManager:
    """Return the process-wide plugin manager (raises if plugins are disabled)."""
    manager: PluginManager | None = request.app.state.plugin_manager
    if manager is None:
        from app.services.plugins import PluginError

        raise PluginError("The plugin system is disabled.")
    return manager


PluginManagerDep = Annotated[PluginManager, Depends(get_plugin_manager)]


def get_tool_registry(request: Request) -> ToolRegistry:
    """Return the process-wide tool registry built at startup."""
    registry: ToolRegistry = request.app.state.tool_registry
    return registry


ToolRegistryDep = Annotated[ToolRegistry, Depends(get_tool_registry)]


def get_tool_engine(session: DbSession, request: Request) -> ToolExecutionEngine:
    """Build a per-request tool engine bound to the request's DB session.

    The registry and permission policy are shared (stateless); only the audit
    repository is request-scoped.
    """
    registry: ToolRegistry = request.app.state.tool_registry
    policy: PermissionPolicy = request.app.state.permission_policy
    return ToolExecutionEngine(
        registry, policy, events=EventRepository(session), event_bus=get_event_bus(request)
    )


ToolEngineDep = Annotated[ToolExecutionEngine, Depends(get_tool_engine)]
