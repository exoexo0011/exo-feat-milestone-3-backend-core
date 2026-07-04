# EXO Roadmap

## Vision

EXO is a modular, production-grade desktop AI assistant. It pairs a local
FastAPI backend (layered API → services → repositories → models) with an
Electron + React frontend, talking over REST and WebSockets. The design goals
are: no vendor lock-in (all models behind an `AIProvider` interface), safe local
capabilities (permissioned, sandboxed, confirmation-gated tools), and
extensibility via plugins.

## Status

- **Current version:** 0.6.0
- **Current milestone:** Milestone 6 - Tool Framework (completed)
- **Next milestone:** Milestone 7 - Frontend chat UI + Electron backend lifecycle
- **Estimated overall completion:** ~68%

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

## In progress

- [ ] None (M6 complete; awaiting review before M7).

## Remaining milestones

- [ ] **M7 - Frontend & desktop:** real chat UI (sidebar, history, settings,
  markdown), Zustand stores, typed REST client + WebSocket hook, tool
  confirmation UI, and Electron backend lifecycle (spawn/manage the Python
  server in packaged builds).
- [ ] **M8 - Plugin system:** `PluginManager`, manifest validation, capability
  scoping, plugin-contributed tools/routes discovered at startup.
- [ ] **M9 - Documentation & packaging:** `docs/api.md`, `docs/installation.md`,
  `docs/developer-guide.md`, installers, release pipeline.

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

- Frontend is a placeholder shell; no real chat UI yet.
- `screenshot` tool has no default capture backend (reports "unavailable").
- Clipboard/launch tools depend on platform CLIs/allow-lists and are unverified
  in headless CI (covered by unit tests via injected backends).
- Single local user profile only.

## Completion by area

| Area | Progress |
|---|---|
| Backend core | 95% |
| AI system | 90% |
| Chat system | 85% |
| Tool system | 90% |
| Plugin system | 0% |
| Frontend | 10% |
| Documentation | 60% |
| **Overall** | **~68%** |
