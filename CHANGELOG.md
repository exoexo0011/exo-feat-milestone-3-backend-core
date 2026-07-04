# Changelog

All notable changes to EXO are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/) (pre-1.0: each milestone
is a minor release).

## [Unreleased]

- Milestone 7 (frontend chat UI + Electron backend lifecycle) not yet started.

## [0.6.0] - 2026-07-04 - Milestone 6: Tool Framework

### Added

- Tool framework under `app/services/tools/`:
  - `BaseTool` abstraction with Pydantic-validated parameters, declared
    permissions, a `requires_confirmation` flag, and `spec()` for AI
    tool-calling / UI.
  - `ToolRegistry` (name-indexed lookup and discovery).
  - `PermissionPolicy` (hard allow/deny by capability category).
  - `FileSandbox` (root confinement, path-traversal protection, size caps).
  - Injectable OS backends: `Clock`, `ClipboardBackend`, `UrlOpener`,
    `Screenshotter`, `AppLauncher`.
  - `ToolExecutionEngine`: validate → authorise → confirm → run → audit, with a
    confirmation lifecycle recorded via `AssistantAction`.
- 13 built-in tools: `calculator`, `current_time`, `clipboard`, `open_url`,
  `read_file`, `write_file`, `list_directory`, `search_files`, `create_folder`,
  `move_files`, `delete_files`, `screenshot`, `launch_application`.
- REST endpoints under `/api/tools` (list, execute, confirm, deny, history).
- Tool settings: `tool_fs_allowed_roots`, `tool_max_file_bytes`,
  `tool_allowed_apps`, `tool_denied_permissions`.
- `EventRepository.get_action` and `list_actions` for tool history.
- Documentation: `docs/tools.md`; project-management documents
  (CHANGELOG, ROADMAP, TODO, ARCHITECTURE, DECISIONS, KNOWN_ISSUES,
  PROJECT_STATUS).
- `frontend/package-lock.json` committed for reproducible installs.

### Changed

- Package version bumped to `0.6.0` to align with milestone numbering.
- Frontend `postcss.config.js` and `tailwind.config.js` renamed to `.mjs`.

### Fixed

- Message ordering under coarse OS timer resolution: added a monotonic
  autoincrement `seq` key to `Message` and order by it (wall-clock `created_at`
  could collide, making the chat context window nondeterministic).
- Frontend `MODULE_TYPELESS_PACKAGE_JSON` build warning.

### Security

- Filesystem tools are sandboxed and deny access when no roots are configured.
- Application launcher is deny-by-default (empty allow-list).
- Destructive/irreversible tools require explicit confirmation.

### Performance

- Blocking OS/tool I/O dispatched to worker threads (`asyncio.to_thread`) to
  avoid blocking the event loop.

### Breaking changes

- `Message` primary key is now the integer `seq`; the string `id` remains the
  stable external identifier. Internal-only change (no API/schema impact); the
  SQLite schema is created fresh, so no migration is required in Phase 1.

### Dependencies

- Added `httpx==0.28.1` (runtime) and `tzdata==2026.2` (IANA timezone data for
  `zoneinfo` on Windows / minimal images).

## [0.5.0] - 2026-07-04 - Milestone 5: Chat Pipeline

### Added

- `ChatService` orchestrating a chat turn (persist user message → build context
  → call provider → persist assistant reply with provider/usage metadata),
  with single-shot and streaming paths.
- `MemoryService` for conversation context management (system prompt + recency
  window; tool-role messages excluded).
- `ConversationRepository.list_recent_messages` for context windowing.
- REST endpoints under `/api/chat` (create/list conversations, list messages,
  send message).
- WebSocket `/ws/chat` for token streaming with a done/error protocol.
- Chat settings: `chat_system_prompt`, `chat_max_context_messages`.
- Documentation: `docs/chat.md`.

### Changed

- AI provider is created once in the application lifespan (`app.state`) and
  closed on shutdown, so HTTP providers reuse a single connection pool.
- Added an `AIProvider.model` property (overridden by echo/HTTP providers).

### Fixed

- Pinned `pytest` `asyncio_default_fixture_loop_scope = "function"` to remove a
  deprecation warning.

### Performance

- Shared provider connection pool across requests/WebSockets.

## [0.4.0] - 2026-07-04 - Milestone 4: AI Provider Architecture

### Added

- Vendor-agnostic `AIProvider` interface with single-shot `generate` and
  streaming `stream`; value types `ChatMessage`, `CompletionResult`,
  `StreamChunk`, `Usage`; provider error hierarchy.
- `ProviderFactory` with decorator-based auto-registration (Open/Closed).
- `HttpChatProvider` base managing the `httpx` client lifecycle with JSON/SSE
  helpers and client injection for testing.
- Providers: `EchoProvider` (no key/network), `OpenAIProvider`,
  `AnthropicProvider`.
- AI settings (`ai_provider`, `ai_model`, `ai_temperature`, `ai_max_tokens`,
  `ai_request_timeout`) and OpenAI/Anthropic keys (accepting both `EXO_`-prefixed
  and conventional env names).
- Documentation: `docs/ai-providers.md`.

### Dependencies

- Added `httpx` as a runtime dependency.

## [0.3.0] - Milestone 3: Backend Core (pre-existing baseline)

### Added

- SQLAlchemy models (users/preferences, conversations/messages,
  system events/assistant actions), repositories, and Pydantic schemas.
- Async SQLite session management, domain exception handling.

## [0.1.0] - Milestones 1-2: Foundation & Stack Wiring (pre-existing baseline)

### Added

- Project scaffolding, configuration, logging, CI, Docker, bootstrap scripts.
- FastAPI app factory, `/api/health` endpoint, and the frontend skeleton shell
  verifying the full stack.

[Unreleased]: https://gitlab.com/exo-group9325627/exo/-/compare/v0.6.0...HEAD
[0.6.0]: https://gitlab.com/exo-group9325627/exo/-/releases/v0.6.0
[0.5.0]: https://gitlab.com/exo-group9325627/exo/-/releases/v0.5.0
[0.4.0]: https://gitlab.com/exo-group9325627/exo/-/releases/v0.4.0
