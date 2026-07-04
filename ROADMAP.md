# EXO Roadmap

## Vision

EXO is a modular, production-grade desktop AI assistant. It pairs a local
FastAPI backend (layered API → services → repositories → models) with an
Electron + React frontend, talking over REST and WebSockets. The design goals
are: no vendor lock-in (all models behind an `AIProvider` interface), safe local
capabilities (permissioned, sandboxed, confirmation-gated tools), and
extensibility via plugins.

## Status

- **Current version:** 0.8.0
- **Current milestone:** Milestone 8 - Plugin Framework (completed)
- **Next milestone:** Milestone 9 - Documentation & packaging
- **Estimated overall completion:** ~90%

## Completed milestones

- [x] **M1 - Foundation:** repo layout, config, logging, DB session, exceptions,
  CI, Docker, bootstrap scripts.
- [x] **M2 - Stack wiring:** FastAPI app factory, `/api/health`, frontend
  skeleton verifying the full stack.
- [x] **M3 - Backend core:** models, repositories, schemas (users, conversations,
  messages, events, assistant actions).
- [x] **M4 - AI provider architecture:** `AIProvider` interface, `ProviderFactory`,
  Echo/OpenAI/Anthropic providers, sync + streaming.
- [x] **M5 - Chat pipeline:** `ChatService`, `MemoryService`, context management,
  REST chat endpoints, WebSocket streaming.
- [x] **M6 - Tool framework:** BaseTool, registry, permissions, sandbox,
  confirmation, execution engine, history, 13 built-in tools, tools REST API.
- [x] **M7 - Desktop UI & Electron:** full React chat UI (sidebar/history/search,
  streaming, markdown + syntax highlighting + copy, attachments + drag-drop,
  settings, theme switching, notifications, indicators, shortcuts, a11y),
  Zustand stores, typed REST + WebSocket clients, and Electron integration
  (backend process manager + auto-restart, secure IPC, native notifications,
  system tray, window-state persistence). Vitest test suite.
- [x] **M8 - Plugin framework:** EventBus, plugin manifest + permissions +
  version compatibility, PluginContext (DI), registry/loader/manager with
  lifecycle, dependency ordering, failure isolation, enable/disable/reload,
  plugin API (tools/commands/routes/ws/settings/ui/hooks/events), SDK, example
  plugin, and plugins REST API.

## In progress

- [ ] None (M8 complete; awaiting review before M9).

## Remaining milestones

- [ ] **M9 - Documentation & packaging:** `docs/api.md`, `docs/installation.md`,
  `docs/developer-guide.md`, installers, release pipeline, real E2E tests.
- [ ] **Chat tool-calling loop:** let the model invoke tools during a chat turn
  and stream `tool` events to the (already built) UI indicators.
- [ ] **Plugin isolation hardening:** subprocess/WASM sandboxing for true
  process isolation; route teardown on disable.

> Note: milestone numbering follows the delivery order agreed in this project.
> The plugin system (originally referenced as "Milestone 6" in early notes) is
> now scheduled as M8, after the frontend.

## Future ideas

- Additional AI providers (local models via Ollama/llama.cpp, Azure OpenAI,
  Google Gemini).
- Tool-calling loop: let the model invoke tools during a chat turn.
- Conversation summarisation for long-context memory.
- Retrieval-augmented memory (embeddings + vector store).
- Multi-profile / multi-user support beyond the single default profile.
- Screenshot capture backend (mss/Pillow) and richer system integrations.

## Long-term goals

- Signed, auto-updating desktop installers for Windows/macOS/Linux.
- A stable plugin API and a small ecosystem of community plugins.
- Optional authenticated remote mode (currently local-first, unauthenticated).
- Test coverage tracking with an enforced threshold in CI.

## Technical debt

- No database migrations (schema via `create_all`); Alembic needed before any
  schema evolution on existing databases.
- No authentication/authorization on the REST/WebSocket surface (acceptable for
  local-first, but blocks remote exposure).
- Test coverage is not measured yet (no `pytest-cov` configured).
- `db_path` default resolves relative to the working directory.
- Only a catch-all handler for `ExoError`; unhandled exceptions fall through to
  the framework default.

## Known limitations

- `screenshot` tool has no default capture backend (reports "unavailable").
- Clipboard/launch tools depend on platform CLIs/allow-lists and are unverified
  in headless CI (covered by unit tests via injected backends).
- Single local user profile only.
- Tool-execution UI indicators exist but the backend does not yet emit `tool`
  stream events (arrives with the chat tool-calling loop).
- Electron packaged flow (backend spawn, tray icon asset, real E2E) is
  implemented and compiles but is not exercised in this headless environment.
- File attachments are folded into the message text (text files only); binary
  files are noted but not uploaded.
- Plugins run in-process: permissions are enforced at the PluginContext boundary
  but there is no true OS sandbox (only trusted plugins should be installed).
- Plugin-mounted API routes persist until restart (disable stops tools/commands/
  events/hooks but not already-mounted routes).
- Plugin settings are in-memory (not persisted across restarts yet).

## Completion by area

| Area | Progress |
|---|---|
| Backend core | 97% |
| AI system | 90% |
| Chat system | 85% |
| Tool system | 92% |
| Plugin system | 90% |
| Frontend | 85% |
| Documentation | 70% |
| **Overall** | **~90%** |
