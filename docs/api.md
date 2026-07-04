# EXO API Reference

The backend exposes a REST API under `/api` and a streaming WebSocket at
`/ws/chat`. Interactive docs (Swagger UI / ReDoc) are served at `/docs` and
`/redoc` when the backend is running.

- **Base URL (dev):** `http://127.0.0.1:8000`
- **Content type:** `application/json` for all REST requests/responses.
- **Auth:** none. EXO is local-first and unauthenticated; do not expose the
  backend beyond `localhost` without adding an authentication layer.

## Error format

Domain errors return a consistent JSON envelope with an appropriate status code:

```json
{ "detail": "Conversation 'abc' not found" }
```

| Status | Meaning |
|---|---|
| 400 | Bad request / generic domain error |
| 403 | Permission denied (tool/plugin) |
| 404 | Entity not found |
| 409 | Conflict (e.g. version/dependency) |
| 422 | Validation error (bad request body / arguments) |
| 500 | Internal error (e.g. tool execution failure) |
| 502 | Upstream AI provider error |

Request-body validation errors (FastAPI) use the standard `422` shape with a
`detail` array describing each invalid field.

---

## Health

### `GET /api/health`

Liveness plus a database round-trip check.

```json
{ "status": "ok", "version": "0.9.0", "env": "development", "database": "ok" }
```

`status` is `ok` or `degraded`; `database` is `ok` or `error`.

---

## Chat

### `POST /api/chat/conversations`

Create a conversation. Body: `{ "title": "New chat" }` (title 1–255 chars).
Returns `201` with a `ConversationRead`:

```json
{
  "id": "…", "title": "New chat", "archived": false,
  "created_at": "2026-07-04T12:00:00Z", "updated_at": "2026-07-04T12:00:00Z"
}
```

### `GET /api/chat/conversations?include_archived=false`

List conversations, most recently updated first. Returns `ConversationRead[]`.

### `GET /api/chat/conversations/{conversation_id}/messages`

Full message history (oldest first). Returns `MessageRead[]`:

```json
{
  "id": "…", "conversation_id": "…", "role": "assistant",
  "content": "Hello!", "meta": { "provider": "echo", "model": "echo" },
  "token_count": 1, "created_at": "2026-07-04T12:00:01Z"
}
```

`role` is one of `user`, `assistant`, `system`, `tool`.

### `POST /api/chat/conversations/{conversation_id}/messages`

Send a user message and get the assistant's (non-streaming) reply. Body:
`{ "content": "Hello" }` (non-empty). Returns a `ChatResponse`:

```json
{
  "message": { "…": "MessageRead (assistant)" },
  "provider": "echo",
  "model": "echo",
  "finish_reason": "stop",
  "usage": { "prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4 }
}
```

`usage` may be `null` when the provider does not report token counts. Unknown
`conversation_id` → `404`; empty `content` → `422`.

---

## Chat streaming (WebSocket)

### `GET /ws/chat`

Bidirectional streaming. The client sends one JSON frame per turn:

```json
{ "conversation_id": "…", "content": "Hello" }
```

The server responds with a sequence of frames:

```json
{ "type": "token", "delta": "He" }
{ "type": "token", "delta": "llo" }
{ "type": "done", "message": { "…": "MessageRead" }, "provider": "echo", "model": "echo", "finish_reason": "stop" }
```

Errors are reported without closing the socket, so the client may retry on the
same connection:

```json
{ "type": "error", "detail": "Conversation '…' not found" }
```

The assistant message is persisted only after the stream completes; an
interrupted stream leaves no partial reply. If the client disconnects
mid-stream the server abandons the turn cleanly.

---

## Tools

### `GET /api/tools`

List registered tools (built-in + plugin-contributed). Returns `ToolSpec[]`:

```json
{
  "name": "calculator",
  "description": "Evaluate a basic arithmetic expression …",
  "requires_confirmation": false,
  "permissions": [],
  "parameters": { "…": "JSON Schema of the tool's parameters" }
}
```

### `POST /api/tools/{name}/execute`

Execute a tool. Body:

```json
{ "arguments": { "expression": "2+2" }, "confirm": false, "conversation_id": null }
```

Returns a `ToolResultResponse`:

```json
{ "tool": "calculator", "status": "completed", "output": { "result": 4 }, "error": null, "action_id": "…" }
```

`status` is one of:

- `completed` — success; see `output`.
- `failed` — validation or execution error; see `error`.
- `denied` — a required permission is denied by policy.
- `confirmation_required` — the tool needs confirmation; resend with
  `confirm: true` or use the confirm endpoint with the returned `action_id`.

Unknown tool → `404`.

### `POST /api/tools/actions/{action_id}/confirm`

Confirm and run a pending (`confirmation_required`) action. Returns a
`ToolResultResponse`.

### `POST /api/tools/actions/{action_id}/deny`

Reject a pending action without running it. Returns a `ToolResultResponse` with
`status: "denied"`.

### `GET /api/tools/history?limit=50`

Recent tool invocations from the audit trail (newest first). Returns
`AssistantActionRead[]`:

```json
{
  "id": "…", "conversation_id": null, "tool_name": "calculator",
  "arguments": { "expression": "2+2" }, "result": { "result": 4 },
  "status": "completed", "created_at": "…", "completed_at": "…"
}
```

---

## Plugins

### `GET /api/plugins`

List discovered plugins. Returns `PluginInfo[]`:

```json
{
  "name": "hello_exo", "state": "enabled", "version": "1.0.0",
  "author": "EXO Team", "description": "…",
  "permissions": ["tool_access", "notifications"], "dependencies": [], "error": null
}
```

`state` is one of `discovered`, `enabled`, `disabled`, `error`.

### `GET /api/plugins/{name}`

One plugin's `PluginInfo`. Unknown name → `404`.

### `POST /api/plugins/{name}/enable` · `/disable` · `/reload`

Lifecycle control; each returns the updated `PluginInfo`.

### `GET /api/plugins/commands`

Commands contributed by enabled plugins. Returns `CommandInfo[]`
(`{ plugin, name, description }`).

### `POST /api/plugins/commands/{plugin}/{name}`

Invoke a plugin command. Body: `{ "arguments": { … } }`. Returns
`{ "result": … }` (the command's return value). Unknown command → `404`.

### `GET /api/plugins/settings-pages` · `/ui-panels`

UI contributions from enabled plugins (`{ plugin, id, title, schema }` and
`{ plugin, id, title, location }` respectively).

---

## Configuration

All behaviour is configured via `EXO_*` environment variables (or a `.env`
file). See [installation.md](./installation.md) for the full list, and the
subsystem docs for provider ([ai-providers.md](./ai-providers.md)), tool
([tools.md](./tools.md)) and plugin ([plugins.md](./plugins.md)) settings.
