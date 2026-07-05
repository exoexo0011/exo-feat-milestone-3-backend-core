# Changelog

All notable changes to EXO are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/) (pre-1.0: each milestone
is a minor release).

## [Unreleased]

- Chat tool-calling loop and true plugin sandboxing not yet started.

## [0.9.0] - 2026-07-04 - Milestone 9: Documentation & Packaging

### Added

- Desktop packaging: PyInstaller bundles the backend
  (`backend/packaging/exo_backend.py` + `exo-backend.spec`); electron-builder
  (`frontend/electron-builder.yml`) produces Windows NSIS / macOS dmg / Linux
  AppImage installers shipping the backend bundle and `plugins/` as extra
  resources. Build scripts `scripts/package.sh` / `scripts/package.ps1` and npm
  `pack`/`dist`/`electron:build` scripts.
- End-to-end tests: Playwright (`frontend/e2e/smoke.spec.ts`,
  `playwright.config.ts`) driving the full stack (renderer -> backend, echo
  provider) via managed dev servers.
- Documentation: `docs/api.md` (REST + WebSocket reference),
  `docs/installation.md`, `docs/developer-guide.md`, `docs/migration-guide.md`,
  and `RELEASE_NOTES.md`.
- CI: `frontend:test` (Vitest) and `electron:compile` in build; a Playwright
  `e2e` stage; and a tag-triggered `release` stage that builds artifacts.
- Durable audit trail: lifecycle events (startup/shutdown, plugin
  load/enable/disable/error) are persisted to the `system_events` table via the
  event bus (`app/services/audit.py`) and exposed at `GET /api/system/events`.
  This wires the previously latent M3 audit model into the running app.

### Changed

- `electron/backend.ts` launches the bundled `exo-backend` executable in
  packaged builds (with `EXO_*` env pointing data/logs at the writable per-user
  `userData` directory) and keeps `python -m uvicorn` for development.
- Package versions aligned to `0.9.0` (backend + frontend).

### Fixed

- Chat WebSocket: a client disconnecting mid-stream no longer raises an
  unhandled `RuntimeError` in the ASGI task; sends after close are normalised to
  a clean disconnect (found via the new E2E run).

### Dependencies

- Added (backend dev, build-only): `pyinstaller==6.21.0`.
- Added (frontend dev): `electron-builder`, `@playwright/test`.

## [0.8.0] - 2026-07-04 - Milestone 8: Plugin Framework

### Added

- Event system: an in-process `EventBus` (pub/sub) with sync/async handlers,
  wildcard subscription, and per-handler error isolation. Event names for
  system, plugin lifecycle, chat and tool events.
- Plugin framework (`app/services/plugins/`):
  - `PluginManifest` (validated `plugin.json`) with name/version/author/
    description, permissions, dependencies, `min_exo_version`, entry point.
  - `PluginPermission` set: filesystem read/write, clipboard, network,
    notifications, tool access, settings access.
  - `PluginContext` (dependency injection) with permission-gated registration of
    tools, commands, API routers, WebSocket handlers, settings pages, UI panels,
    startup/shutdown hooks, and event subscriptions.
  - `PluginRegistry` + `PluginRecord` lifecycle states; `PluginLoader`
    (discovery, safe importlib loading under unique module names); `PluginManager`
    (dependency ordering, version compatibility, enable/disable/reload, hooks).
  - Plugin SDK (`app/services/plugins/sdk.py`) as the stable author surface.
- Plugins REST API under `/api/plugins` (list, get, enable, disable, reload,
  commands, execute command, settings-pages, ui-panels).
- Event emission wired into `ChatService` (chat events) and
  `ToolExecutionEngine` (tool events); `system.startup`/`system.shutdown` from
  the app lifespan.
- Reference plugin `plugins/hello_exo/` (tool + command + event subscriber +
  settings page + UI panel + hooks) and `docs/plugins.md` development guide.
- Settings: `plugins_enabled`, `plugins_dir`.
- `ToolRegistry.unregister`, `EventRepository.get_action`/`list_actions`
  (added earlier) supporting plugin/tool teardown and history.

### Changed

- Package versions aligned to `0.8.0` (backend + frontend).
- `ChatService` and `ToolExecutionEngine` accept an optional `event_bus`
  (backward compatible; default `None`).

### Security

- Plugin capabilities are validated and enforced at the `PluginContext`
  boundary; plugin tools must hold permissions matching their tool capabilities.
- Plugin load/register/hook failures are isolated - a bad plugin cannot crash
  the app or affect other plugins.
- Documented limitation: plugins run in-process (no true OS sandbox).

## [0.7.0] - 2026-07-04 - Milestone 7: Desktop UI & Electron Integration

### Added

- Complete React desktop interface (ChatGPT-style):
  - Sidebar with conversation history, new-chat, and live search.
  - Chat window with streaming messages, markdown rendering (GFM), syntax
    highlighting, and per-block copy-to-clipboard.
  - Message input with file attachments and drag-and-drop, auto-grow, and a
    stop-generation control.
  - Settings modal with Light/Dark/System theme switching and an Enter-to-send
    toggle.
  - Toast notification system, typing and tool-execution indicators, loading
    states, a React error boundary, and keyboard shortcuts
    (Ctrl/Cmd+N/K/comma, Esc).
  - Accessibility: ARIA roles/labels, focus management, keyboard navigation.
- Frontend architecture:
  - Zustand stores (`chat`, `settings` [persisted], `ui`).
  - Typed REST client (`api/client.ts`) and WebSocket streaming client
    (`api/chatSocket.ts`) matching the backend contracts.
  - Reusable, accessible components and a self-contained inline SVG icon set.
- Electron integration:
  - Backend process manager with health-checking and auto-restart (capped).
  - Secure IPC bridge via a context-isolated preload (`window.exo`).
  - Native OS notifications, system tray (show/hide/quit), and window-state
    persistence.
- Frontend test suite: Vitest + Testing Library (23 tests across client, stores
  and components) with a jsdom setup.

### Changed

- Package versions aligned to `0.7.0` (backend + frontend).
- Vite build splits vendor chunks (`react`, `markdown`) and raises the chunk
  size hint (locally-loaded desktop bundle).

### Fixed

- Eliminated the Vite chunk-size build warning via manual vendor chunking.

### Security

- Electron renderer runs with `contextIsolation`, `sandbox`, and no node
  integration; all privileged actions go through explicit IPC channels.

### Performance

- Streaming UI updates via incremental token application; memoised markdown
  rendering; code-split vendor bundles.

### Dependencies

- Added (frontend runtime): `zustand`, `react-markdown`, `remark-gfm`,
  `rehype-highlight`, `highlight.js`.
- Added (frontend dev): `vitest`, `@testing-library/react`,
  `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`.
- Evaluated and rejected `lucide-react` (version anomaly for the environment);
  replaced with an inline SVG icon set.

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

[Unreleased]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.9.0
[0.8.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.8.0
[0.7.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.7.0
[0.6.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.6.0
[0.5.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.5.0
[0.4.0]: https://github.com/exoexo0011/exo-feat-milestone-3-backend-core/releases/tag/v0.4.0
