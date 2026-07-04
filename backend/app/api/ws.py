"""WebSocket endpoint for streaming chat responses.

Protocol (JSON frames):

* Client -> server: ``{"conversation_id": "...", "content": "..."}``
* Server -> client: a sequence of ``{"type": "token", "delta": "..."}`` frames
  followed by one ``{"type": "done", "message": {...}, ...}`` frame.
* Errors are reported as ``{"type": "error", "detail": "..."}`` without closing
  the socket, so the client may retry on the same connection.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import DbSession, build_chat_service
from app.config import get_settings
from app.core.exceptions import ExoError
from app.schemas.chat import ChatSocketRequest, DoneEvent, ErrorEvent, TokenEvent
from app.schemas.conversation import MessageRead
from app.services.ai.base import AIProvider
from app.services.chat import ChatDone, ChatToken

logger = logging.getLogger("exo.ws.chat")

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, session: DbSession) -> None:
    """Stream assistant replies token-by-token over a WebSocket."""
    await websocket.accept()
    provider: AIProvider = websocket.app.state.ai_provider
    chat_service = build_chat_service(
        session, provider, get_settings(), websocket.app.state.event_bus
    )

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                request = ChatSocketRequest.model_validate(raw)
            except ValidationError:
                await _send(websocket, ErrorEvent(detail="Invalid request payload."))
                continue

            try:
                async for event in chat_service.stream_message(
                    request.conversation_id, request.content
                ):
                    if isinstance(event, ChatToken):
                        await _send(websocket, TokenEvent(delta=event.delta))
                    elif isinstance(event, ChatDone):
                        await _send(
                            websocket,
                            DoneEvent(
                                message=MessageRead.model_validate(event.message),
                                provider=event.provider,
                                model=event.model,
                                finish_reason=event.finish_reason,
                            ),
                        )
            except WebSocketDisconnect:
                # Client went away mid-stream; abandon this turn cleanly.
                raise
            except ExoError as exc:
                # Expected domain errors (e.g. unknown conversation).
                await _safe_send(websocket, ErrorEvent(detail=exc.message))
            except Exception:
                logger.exception("Unexpected error during chat stream")
                await _safe_send(websocket, ErrorEvent(detail="Internal error during generation."))
    except WebSocketDisconnect:
        logger.debug("Chat WebSocket disconnected")


async def _send(websocket: WebSocket, event: TokenEvent | DoneEvent | ErrorEvent) -> None:
    """Serialise a Pydantic event and send it.

    If the client has already disconnected, the underlying send raises; we
    normalise that to :class:`WebSocketDisconnect` so the caller unwinds cleanly
    instead of crashing the ASGI task.
    """
    try:
        await websocket.send_json(event.model_dump(mode="json"))
    except RuntimeError as exc:  # Starlette raises this when sending after close.
        raise WebSocketDisconnect() from exc


async def _safe_send(websocket: WebSocket, event: TokenEvent | DoneEvent | ErrorEvent) -> None:
    """Best-effort send that ignores a already-closed connection."""
    try:
        await _send(websocket, event)
    except WebSocketDisconnect:
        logger.debug("Skipped send to a closed WebSocket")
