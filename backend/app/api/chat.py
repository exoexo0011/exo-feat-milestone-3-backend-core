"""REST endpoints for conversations and chat turns."""

from fastapi import APIRouter, status

from app.api.deps import ChatServiceDep, DbSession
from app.repositories.conversations import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse, ChatUsage
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    MessageRead,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(payload: ConversationCreate, session: DbSession) -> ConversationRead:
    """Start a new conversation."""
    conversation = await ConversationRepository(session).create(payload.title)
    return ConversationRead.model_validate(conversation)


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    session: DbSession, include_archived: bool = False
) -> list[ConversationRead]:
    """List conversations, most recently updated first."""
    conversations = await ConversationRepository(session).list_conversations(
        include_archived=include_archived
    )
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(conversation_id: str, session: DbSession) -> list[MessageRead]:
    """Return the full message history for a conversation (oldest first)."""
    messages = await ConversationRepository(session).list_messages(conversation_id)
    return [MessageRead.model_validate(m) for m in messages]


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str, payload: ChatRequest, chat_service: ChatServiceDep
) -> ChatResponse:
    """Send a user message and return the assistant's (non-streaming) reply."""
    turn = await chat_service.send_message(conversation_id, payload.content)
    usage = turn.completion.usage
    return ChatResponse(
        message=MessageRead.model_validate(turn.message),
        provider=turn.completion.provider,
        model=turn.completion.model,
        finish_reason=turn.completion.finish_reason,
        usage=(
            ChatUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
            if usage is not None
            else None
        ),
    )
