# EXO Architecture

Living architecture document, kept in sync with the codebase. High-level
overview lives here; subsystem detail is in `docs/` (`ai-providers.md`,
`chat.md`, `tools.md`).

**Version:** 0.9.0 · **Last updated:** 2026-07-04 (Milestone 9)

## 1. System overview

EXO is a local client/server desktop application.

```
┌─────────────────────────────┐        REST /api/*  (CRUD, tools)
│  Frontend (Electron + React) │  ───────────────────────────────►  ┌────────────────────┐
│  - renderer (React/TS/Tail)  │        WebSocket /ws/chat (stream)  │  Backend (FastAPI) │
│  - main/preload (secure)     │  ◄───────────────────────────────  │  localhost:8000    │
└─────────────────────────────┘                                     └─────────┬──────────┘
                                                                               │
                                                                     SQLite (SQLAlchemy async)
```

- **Frontend:** Electron shell (contextIsolation on, sandbox on, no node
  integration) hosting a React + TypeScript + Tailwind renderer with a full
  ChatGPT-style UI, Zustand state, and typed REST/WebSocket clients (see §10).
- **Backend:** FastAPI on localhost exposing REST + WebSocket APIs.
- **Storage:** SQLite via SQLAlchemy async (conversations, messages, profiles,
  preferences, system events, assistant/tool actions).

## 2. Backend layering

```
api/ (routers)  →  services/  →  repositories/  →  models/ (SQLAlchemy)
                     │
                     ├── ai/       AIProvider interface + ProviderFactory + providers
                     ├── chat.py   ChatService (turn orchestration)
                     ├── memory.py MemoryService (context window)
                     └── tools/    BaseTool + registry + permissions + sandbox
                                   + engine + built-in tools
```

Principles:

- Routers never touch the database directly; they depend on services or
  repositories via DI (`app/api/deps.py`).
- All external models sit behind `AIProvider` — no vendor lock-in.
- Every tool declares a Pydantic schema, required permissions, and a
  `requires_confirmation` flag; destructive/irreversible actions are gated by a
  confirmation flow and a filesystem sandbox.
- Domain errors (`ExoError` subclasses) are translated to JSON by a single
  handler, keeping HTTP concerns out of services.

## 3. Module map

| Module | Responsibility |
|---|---|
| `app/main.py` | App factory + lifespan (logging, DB init, provider + tool registry on `app.state`) |
| `app/config.py` | `Settings` (env `EXO_*` / `.env`), cached |
| `app/db/session.py` | Async engine/session, FK enforcement |
| `app/models/` | ORM: `UserProfile`, `Preference`, `Conversation`, `Message`, `SystemEvent`, `AssistantAction` |
| `app/repositories/` | Data access: conversations, users, events |
| `app/schemas/` | Pydantic request/response models |
| `app/api/` | Routers: `health`, `chat`, `tools`, `ws`; `deps.py` DI |
| `app/services/ai/` | `AIProvider`, `ProviderFactory`, `HttpChatProvider`, Echo/OpenAI/Anthropic |
| `app/services/chat.py` | `ChatService` (persist → context → provider → persist) |
| `app/services/memory.py` | `MemoryService` (system prompt + recency window) |
| `app/services/tools/` | Tool framework + `builtins/` (13 tools) |
| `app/services/eventbus.py` | In-process pub/sub `EventBus` + event names |
| `app/services/audit.py` | Persists lifecycle events to the `system_events` table |
| `app/services/plugins/` | Plugin manifest, context, registry, loader, manager, SDK |

## 4. Data flow

### Chat turn (non-streaming, `POST /api/chat/conversations/{id}/messages`)

1. Router resolves `ChatService` (session + shared provider).
2. `ChatService` persists the user message.
3. `MemoryService` builds context: optional system prompt + recent messages
   (ordered by `Message.seq`).
4. Provider `generate(context)` returns a `CompletionResult`.
5. Assistant message persisted with provider/model/usage metadata.
6. `ChatResponse` returned.

### Chat turn (streaming, `WS /ws/chat`)

1. Client sends `{conversation_id, content}`.
2. `ChatService.stream_message` persists the user message, builds context, and
   streams provider deltas as `{type:"token"}` frames.
3. On completion the assistant message is persisted once, then a
   `{type:"done", message, ...}` frame is sent. Errors → `{type:"error"}`.

### Tool invocation (`POST /api/tools/{name}/execute`)

1. `ToolExecutionEngine.execute` resolves the tool from the registry.
2. Arguments validated against the tool's Pydantic model.
3. `PermissionPolicy` checks required capabilities (denied → `DENIED`).
4. If `requires_confirmation` and not confirmed → a `PENDING`
   `AssistantAction` is recorded and `CONFIRMATION_REQUIRED` returned; the
   client resumes via `/actions/{id}/confirm` or `/deny`.
5. The tool runs (filesystem paths pass through `FileSandbox`; OS effects go
   through injectable backends), and the action is finalised
   (`COMPLETED`/`FAILED`) in the audit trail.

## 5. Public APIs

REST (prefix `/api`):

- `GET /health`
- `POST /chat/conversations`, `GET /chat/conversations`,
  `GET /chat/conversations/{id}/messages`,
  `POST /chat/conversations/{id}/messages`
- `GET /tools`, `POST /tools/{name}/execute`,
  `POST /tools/actions/{id}/confirm`, `POST /tools/actions/{id}/deny`,
  `GET /tools/history`

WebSocket:

- `GET /ws/chat` — token streaming (`token` / `done` / `error` frames).

## 6. Key data model notes

- `Message` uses a monotonic autoincrement `seq` primary key for reliable
  ordering; the string `id` is the stable external identifier.
- `AssistantAction` records every tool invocation and its confirmation state
  (`PENDING → CONFIRMED → COMPLETED/FAILED/DENIED`), serving as tool history.

## 7. Dependencies

Backend runtime: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic`,
`pydantic-settings`, `aiosqlite`, `python-dotenv`, `websockets`, `httpx`,
`tzdata`. Dev: `ruff`, `black`, `mypy`, `pytest`, `pytest-asyncio`.

Frontend: React 18, TypeScript 5, Vite 6, Tailwind 3, Electron 33; ESLint +
Prettier. PostCSS/Tailwind configs are ESM (`.mjs`); the Electron main process
compiles to CommonJS.

## 8. Cross-cutting concerns

- **Security:** local-first, currently unauthenticated. Tool safety via
  permission policy, sandbox, and confirmation. Electron uses secure defaults.
- **Config:** all via `Settings` (`EXO_*` env / `.env`).
- **Logging:** console + rotating file, optional JSON.
- **Concurrency:** blocking OS/tool I/O runs in worker threads; a single async
  DB session per request/WebSocket connection.

## 9. Known architectural gaps

See `KNOWN_ISSUES.md` and `ROADMAP.md` (technical debt): no migrations, no auth,
no coverage tooling, catch-all exception handler pending.

## 10. Frontend architecture (renderer)

```
frontend/src/
├── types/        api.ts (backend contracts), electron.ts (bridge), global.d.ts
├── api/          client.ts (typed REST), chatSocket.ts (WebSocket streaming)
├── stores/       Zustand: chatStore, settingsStore (persisted), uiStore
├── hooks/        useTheme, useKeyboardShortcuts
├── lib/          cx (classnames)
├── components/
│   ├── common/   Button, IconButton, Spinner, Notifications, ErrorBoundary
│   ├── sidebar/  Sidebar (history + search + new chat)
│   ├── settings/ SettingsModal (theme, send-on-enter)
│   ├── chat/     ChatWindow, MessageList, MessageItem, MarkdownMessage,
│   │             CodeBlock (copy), MessageInput (attachments+drag/drop),
│   │             ToolIndicator
│   └── icons.tsx inline SVG icon set
├── App.tsx       shell layout + lifecycle wiring
└── main.tsx      entry (ErrorBoundary + StrictMode, hljs theme)
```

Principles:

- **State:** three focused Zustand stores. `settingsStore` is persisted to
  `localStorage`. Components subscribe to slices to minimise re-renders.
- **Data:** the renderer uses relative URLs (`/api`, `/ws`) so the Vite proxy
  (dev) and the packaged app both reach the local backend. `ApiError` carries
  the backend `detail`.
- **Streaming:** `chatStore.sendMessage` opens a per-turn WebSocket via
  `streamChat`, applies token deltas to `streaming`, and appends the persisted
  message on `done`. The socket constructor is injectable for testing.
- **Rendering:** assistant markdown via `react-markdown` + `remark-gfm` +
  `rehype-highlight`; fenced code blocks get a copy button.
- **Accessibility:** ARIA roles/labels, `aria-live` regions for messages and
  toasts, a radiogroup for theme, focus management on the settings dialog,
  and global keyboard shortcuts.

### Frontend data flow (send a message)

1. `MessageInput` composes text (+ attachments) and calls `chatStore.sendMessage`.
2. The store optimistically appends the user message and opens `streamChat`.
3. `token` events append to `streaming.content` (rendered live in `MessageList`).
4. `done` appends the persisted assistant message and refreshes the sidebar;
   `error` raises a toast and clears streaming.

## 11. Electron integration

```
frontend/electron/
├── main.ts         app lifecycle, window, IPC, tray, notifications
├── preload.ts      secure contextBridge -> window.exo
├── backend.ts      BackendManager: spawn + health-check + auto-restart
├── tray.ts         system tray (show/hide/quit)
└── windowState.ts  persist/restore window bounds (userData JSON)
```

- **Security:** `contextIsolation: true`, `sandbox: true`, `nodeIntegration:
  false`. The renderer only sees the minimal typed `window.exo` bridge.
- **Backend lifecycle:** in packaged builds `BackendManager` spawns
  `uvicorn app.main:app`, polls `/api/health` until ready, auto-restarts on
  crash (capped at 5, with backoff), and reports phase (`starting`/`ready`/
  `error`/`stopped`) to the renderer over the `backend:status` channel. In dev
  the backend is run separately and the main process reports `ready`.
- **IPC channels:** `backend:status` (main→renderer), `backend:getStatus`
  (invoke), `notify` (renderer→main native notification).
- **Windowing:** closing hides to the system tray; bounds are persisted and
  restored across launches.

> The Electron layer compiles cleanly (`tsc -p electron`). As of M9 the backend
> spawn is implemented for both dev (`python -m uvicorn`) and packaged
> (bundled `exo-backend` executable) modes; installer builds run on platform CI
> runners (see §13).

## 12. Event system & plugin framework

```
app/services/
├── eventbus.py           EventBus (pub/sub, error-isolated), EventName
└── plugins/
    ├── manifest.py       PluginManifest, PluginPermission, version helpers
    ├── context.py        PluginContext (DI) + PluginRegistration + descriptors
    ├── registry.py       PluginRegistry, PluginRecord, PluginState
    ├── loader.py         discovery + safe importlib loading
    ├── manager.py        PluginManager (lifecycle + integration)
    ├── sdk.py            stable import surface for plugin authors
    └── errors.py         plugin error hierarchy
```

- **EventBus** decouples producers (chat, tools, plugin lifecycle, system) from
  consumers (plugins). Handlers may be sync or async; exceptions are isolated so
  one subscriber cannot affect the publisher or siblings. It is created once in
  the lifespan and shared via `app.state.event_bus`. `ChatService` and
  `ToolExecutionEngine` publish events when a bus is injected. A durable audit
  recorder (`app/services/audit.py`) subscribes to the bus and persists
  lifecycle events (startup/shutdown, plugin load/enable/disable/error) to the
  `system_events` table, exposed at `GET /api/system/events`.
- **PluginManager** (created in the lifespan when `plugins_enabled`) discovers
  plugin directories under `plugins_dir`, validates manifests, orders by
  dependencies, checks `min_exo_version`, imports each package under a unique
  module name, and calls `register(context)`. Plugin contributions are recorded
  (not applied) during `register`; the manager **applies** them on enable
  (register tools into the `ToolRegistry`, subscribe events, add commands, mount
  routers, run startup hooks) and **reverts** them on disable.
- **Isolation:** every plugin operation is wrapped - an import/register/hook
  failure marks the plugin `error` and never propagates. Permissions are
  enforced at the `PluginContext` boundary; plugins run in-process (no OS
  sandbox - see KNOWN_ISSUES).
- **Surface:** plugins can register tools, commands, API routers, WebSocket
  handlers, settings pages, UI panels, startup/shutdown hooks, and event
  subscriptions. Exposed via `/api/plugins` (list/get/enable/disable/reload/
  commands/settings-pages/ui-panels).

### Plugin lifecycle

```
discovered ──load──► enabled ──disable──► disabled ──enable──► enabled
     │                  │                                        
     └─ manifest/       └─ (reload) unload module + re-register  
        version/dep         
        failure ─────────► error
```

## 13. Packaging, distribution & CI

```
PyInstaller (backend/packaging/exo-backend.spec)
    -> backend/packaging/dist/exo-backend/   (self-contained backend)
electron-builder (frontend/electron-builder.yml)
    -> frontend/release/                     (NSIS / dmg / AppImage)
       extraResources: <resources>/backend, <resources>/plugins
```

- **Backend bundle:** PyInstaller freezes `exo_backend.py` (which runs uvicorn on
  the imported `app`) into a onedir executable.
- **Desktop app:** electron-builder packages the compiled renderer
  (`dist/`) + Electron main (`dist-electron/`) and ships the backend bundle and
  `plugins/` as extra resources. At runtime `electron/backend.ts` spawns
  `<resources>/backend/exo-backend`, health-checks it, and points `EXO_DB_PATH` /
  `EXO_LOG_DIR` at the OS `userData` directory (writable).
- **Build scripts:** `scripts/package.sh` / `scripts/package.ps1` run both steps.
- **CI (`.gitlab-ci.yml`):** stages `lint → test → build → e2e → release`.
  `test` runs pytest + Vitest; `e2e` provisions Python (uv) + Chromium
  (Playwright) and runs the smoke suite; `release` (on tags) builds the backend
  bundle and desktop installer artifacts.
- **E2E:** Playwright starts the backend (echo provider) + Vite dev server via
  managed `webServer`s and drives headless Chromium (`frontend/e2e/`).

> Installer artifact builds and code signing run on platform-specific runners,
> not in the development sandbox.
