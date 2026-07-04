# Chat Pipeline

Milestone 5 connects the persistence layer (Milestone 3) and the AI provider
layer (Milestone 4) into a working chat pipeline, exposed over REST and a
streaming WebSocket.

## Components

```
API (chat.py / ws.py)
      │  depends on
      ▼
ChatService ── uses ──► AIProvider (via ProviderFactory, created at startup)
      │
      ├─ uses ─► MemoryService ── reads ─► ConversationRepository
      └─ writes/reads ──────────────────► ConversationRepository
```

- **`ChatService`** (`app/services/chat.py`) orchestrates a turn: persist the
  user message, ask `MemoryService` for context, call the provider, persist the
  assistant reply with provider/usage metadata. It offers a single-shot path
  (`send_message`) and a streaming path (`stream_message`) that share the same
  persistence logic.
- **`MemoryService`** (`app/services/memory.py`) owns context policy: it builds
  the provider-ready message list as an optional leading system prompt followed
  by a recency window of prior messages (`chat_max_context_messages`). Tool-role
  messages are excluded until the tool system lands (Milestone 6).
- The **provider** is created once in the application lifespan and stored on
  `app.state`, so HTTP-backed providers reuse a single connection pool. It is
  closed on shutdown.

## Configuration

| Setting | Env var | Default |
|---|---|---|
| `chat_system_prompt` | `EXO_CHAT_SYSTEM_PROMPT` | `"You are EXO, a helpful, concise AI desktop assistant."` |
| `chat_max_context_messages` | `EXO_CHAT_MAX_CONTEXT_MESSAGES` | `20` |

Provider selection and generation defaults come from the AI provider settings
documented in [`ai-providers.md`](./ai-providers.md).

## REST API

All routes are under `/api/chat`.

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/conversations` | `{ "title": "..." }` | `201` `ConversationRead` |
| `GET` | `/conversations?include_archived=false` | — | `ConversationRead[]` |
| `GET` | `/conversations/{id}/messages` | — | `MessageRead[]` (oldest first) |
| `POST` | `/conversations/{id}/messages` | `{ "content": "..." }` | `ChatResponse` |

`ChatResponse` contains the persisted assistant `message`, plus `provider`,
`model`, `finish_reason` and optional `usage` (`prompt_tokens`,
`completion_tokens`, `total_tokens`). Unknown conversation ids return `404`;
empty content returns `422`.

### Example

```bash
# Create a conversation
curl -X POST localhost:8000/api/chat/conversations -H 'content-type: application/json' -d '{"title":"Demo"}'

# Send a message
curl -X POST localhost:8000/api/chat/conversations/<id>/messages \
  -H 'content-type: application/json' -d '{"content":"Hello!"}'
```

## WebSocket API

Endpoint: `GET /ws/chat` (WebSocket upgrade).

The client sends one JSON frame per turn:

```json
{ "conversation_id": "<id>", "content": "Hello!" }
```

The server responds with a stream of frames:

```json
{ "type": "token", "delta": "He" }
{ "type": "token", "delta": "llo" }
{ "type": "done", "message": { ...MessageRead... }, "provider": "echo", "model": null, "finish_reason": "stop" }
```

Errors are reported without closing the socket, so the client can retry on the
same connection:

```json
{ "type": "error", "detail": "Conversation 'x' not found" }
```

The assistant message is persisted only once the stream completes, so an
interrupted stream never leaves a partial reply in history.

## Testing

- `tests/test_chat.py` - unit tests for `MemoryService` (system prompt,
  windowing, tool-message exclusion) and `ChatService` (persistence, streaming).
- `tests/test_chat_api.py` - integration tests for the REST endpoints and the
  WebSocket, running against the real app with the deterministic `echo`
  provider.
