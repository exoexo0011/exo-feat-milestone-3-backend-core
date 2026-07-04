# TODO

Live engineering task list. Tasks move to **Completed** as they finish.
Priorities: High (blocks the next milestone or is a correctness/security risk),
Medium (important, not blocking), Low (nice-to-have / hygiene).

## High Priority

- **Frontend chat UI** — Build the real chat interface (message list, input,
  sidebar, streaming rendering) consuming `/api/chat` and `/ws/chat`.
  Status: Not started · Priority: High · Milestone: M7
- **Typed API client + WebSocket hook** — Frontend REST client and streaming
  hook with shared TypeScript types.
  Status: Not started · Priority: High · Milestone: M7
- **Tool confirmation UI** — Surface `confirmation_required` results and wire
  confirm/deny to the tools API.
  Status: Not started · Priority: High · Milestone: M7
- **Electron backend lifecycle** — Spawn and manage the Python backend in
  packaged builds; health-gate the renderer.
  Status: Not started · Priority: High · Milestone: M7

## Medium Priority

- **Database migrations (Alembic)** — Replace `create_all` with migrations
  before any schema change ships to existing databases.
  Status: Not started · Priority: Medium · Milestone: Tech debt
- **Test coverage tooling** — Add `pytest-cov`, report coverage, and set a CI
  threshold.
  Status: Not started · Priority: Medium · Milestone: Tech debt
- **Tool-calling loop** — Let the model request tool execution mid-chat and feed
  results back.
  Status: Not started · Priority: Medium · Milestone: M7/M8
- **Screenshot capture backend** — Provide a real cross-platform capture backend
  (e.g. mss/Pillow) behind the existing `Screenshotter` abstraction.
  Status: Not started · Priority: Medium · Milestone: Future

## Low Priority

- **Catch-all exception handler** — Return a consistent JSON envelope for
  unhandled exceptions.
  Status: Not started · Priority: Low · Milestone: Tech debt
- **CWD-independent `db_path`** — Resolve the default database path independent
  of the current working directory.
  Status: Not started · Priority: Low · Milestone: Tech debt
- **Additional AI providers** — Ollama/local, Azure OpenAI, Gemini.
  Status: Not started · Priority: Low · Milestone: Future

## Completed

- **Tool framework + 13 built-in tools** — BaseTool, registry, permissions,
  sandbox, confirmation, engine, history, tools REST API.
  Status: Done · Priority: High · Milestone: M6
- **Fix message ordering under coarse timers** — Monotonic `seq` key on
  `Message`.
  Status: Done · Priority: High · Milestone: M6
- **Add `tzdata` dependency** — IANA timezone data for `zoneinfo` on Windows.
  Status: Done · Priority: Medium · Milestone: M6
- **Fix frontend module-type build warning** — `.mjs` config files; commit
  `package-lock.json`.
  Status: Done · Priority: Medium · Milestone: M6
- **Chat pipeline** — `ChatService`, `MemoryService`, REST + WebSocket.
  Status: Done · Priority: High · Milestone: M5
- **Shared provider connection pool** — Provider built once in lifespan.
  Status: Done · Priority: Medium · Milestone: M5
- **AI provider architecture** — Interface, factory, Echo/OpenAI/Anthropic,
  streaming.
  Status: Done · Priority: High · Milestone: M4
