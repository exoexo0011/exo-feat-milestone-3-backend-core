"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.conversations import ConversationRepository
from app.services.ai.base import AIProvider
from app.services.chat import ChatService
from app.services.memory import MemoryService

# Request-scoped database session, injected into route handlers.
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_ai_provider(request: Request) -> AIProvider:
    """Return the process-wide provider created during application startup."""
    provider: AIProvider = request.app.state.ai_provider
    return provider


AiProvider = Annotated[AIProvider, Depends(get_ai_provider)]


def build_chat_service(
    session: AsyncSession, provider: AIProvider, settings: Settings
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
    return ChatService(conversations, memory, provider)


def get_chat_service(session: DbSession, provider: AiProvider) -> ChatService:
    """FastAPI dependency providing a fully wired chat service."""
    return build_chat_service(session, provider, get_settings())


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
