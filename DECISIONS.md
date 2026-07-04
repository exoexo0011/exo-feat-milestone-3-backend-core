# Architecture Decision Record (ADR)

Chronological record of significant technical decisions. Newest first.

---

## ADR-0021 - Package with electron-builder + PyInstaller

- **Date:** 2026-07-04 (M9)
- **Decision:** Bundle the backend with PyInstaller (onedir) and package the
  desktop app with electron-builder, shipping the backend bundle + `plugins/` as
  extra resources.
- **Reason:** Both are the mature, standard tools for their layer; end users get
  a single installer needing neither Python nor Node.
- **Alternatives considered:** Tauri (would replace Electron + the whole UI
  layer); electron-forge; embedding a full Python runtime manually.
- **Advantages:** Standard, well-documented, cross-platform; keeps the existing
  Electron/React stack.
- **Disadvantages:** Two build tools; large artifacts; installer build + signing
  require platform runners (not verifiable in the dev sandbox).
- **Impact:** `frontend/electron-builder.yml`, `backend/packaging/`, scripts, CI.

## ADR-0020 - Packaged backend runs as a spawned executable with userData paths

- **Date:** 2026-07-04 (M9)
- **Decision:** In packaged builds the Electron main process spawns the bundled
  `exo-backend` executable and injects `EXO_*` env so the DB and logs live under
  the OS `userData` directory; dev keeps `python -m uvicorn`.
- **Reason:** The install/resources directory is typically read-only; user data
  must go somewhere writable and stable.
- **Alternatives considered:** Write next to the executable (fails on read-only
  installs); embed a Python interpreter and run source directly.
- **Advantages:** Robust on all platforms; clean dev/prod split; no config
  changes for developers.
- **Disadvantages:** Packaged path only exercised on a real install.
- **Impact:** `electron/backend.ts`.

## ADR-0019 - E2E via Playwright against the dev server + live backend

- **Date:** 2026-07-04 (M9)
- **Decision:** Run end-to-end smoke tests with Playwright (headless Chromium)
  against the Vite dev server (which proxies to a live backend on the echo
  provider), orchestrated by Playwright's managed `webServer`s - not full
  Electron GUI automation.
- **Reason:** Exercises the real renderer + REST/WebSocket stack deterministically
  and runs in CI without a display; full Electron GUI automation needs a display
  and is disproportionately fragile.
- **Alternatives considered:** Playwright-Electron driver; Spectron (deprecated).
- **Advantages:** Fast, deterministic, CI-friendly; caught a real WebSocket
  disconnect bug.
- **Disadvantages:** Does not cover the Electron shell itself (window/tray).
- **Impact:** `frontend/playwright.config.ts`, `frontend/e2e/`, CI `e2e` stage.

## ADR-0018 - In-process plugins with permission-boundary enforcement

- **Date:** 2026-07-04 (M8)
- **Decision:** Load plugins in the backend process; enforce declared
  permissions at the `PluginContext` API boundary and validate plugin tool
  capabilities against grants. Do not attempt a true sandbox.
- **Reason:** In-process loading gives plugins first-class access to the tool
  registry, event bus and routers with minimal complexity; boundary enforcement
  plus confirmation flows cover the common cases.
- **Alternatives considered:** Subprocess or WASM isolation (much more complex,
  IPC overhead, limited API surface).
- **Advantages:** Simple, powerful plugin API; fast; easy to test.
- **Disadvantages:** No hard security boundary - a malicious plugin can bypass
  checks by importing modules directly. Documented; only trusted plugins.
- **Impact:** Whole plugin subsystem; recorded as a KNOWN_ISSUE.

## ADR-0017 - Plugin registration is pure recording; manager applies/reverts

- **Date:** 2026-07-04 (M8)
- **Decision:** `register(context)` only records intended contributions; the
  `PluginManager` applies them on enable and reverts on disable.
- **Reason:** Symmetric enable/disable, and a `register` that raises midway
  leaves no partial state (error isolation).
- **Alternatives considered:** Register mutating shared state directly.
- **Advantages:** Clean lifecycle, safe failures, testable.
- **Disadvantages:** Slight indirection; already-mounted routes can't be
  reverted (documented).
- **Impact:** `PluginContext`, `PluginManager`.

## ADR-0016 - Load plugins via importlib file-location under unique module names

- **Date:** 2026-07-04 (M8)
- **Decision:** Import each plugin package from its `__init__.py` under a unique
  `exo_plugins.<name>` module name (not by mutating `sys.path`).
- **Reason:** Avoids import-namespace clashes between plugins and the app; makes
  reload possible (drop and re-exec the module).
- **Alternatives considered:** Adding the plugins dir to `sys.path`.
- **Advantages:** Isolation of module names; supports reload.
- **Disadvantages:** Slightly more code than a bare import.
- **Impact:** `loader.py`.

## ADR-0015 - EventBus with per-handler error isolation

- **Date:** 2026-07-04 (M8)
- **Decision:** A single in-process pub/sub `EventBus`; handlers may be sync or
  async and their exceptions are logged and swallowed.
- **Reason:** Decouple producers from plugin consumers; a faulty subscriber must
  never break chat/tool flows.
- **Alternatives considered:** Direct callbacks; an external broker (overkill for
  a local app).
- **Advantages:** Simple, robust, dependency-free.
- **Disadvantages:** In-process only (no cross-process events).
- **Impact:** `eventbus.py`; chat/tool/system/plugin emitters.

## ADR-0014 - Per-turn WebSocket for streaming

- **Date:** 2026-07-04 (M7)
- **Decision:** Open a fresh WebSocket per chat turn (`streamChat`) rather than a
  persistent socket; inject the `WebSocket` constructor for testing.
- **Reason:** Matches the backend's per-message WS protocol, simplifies lifecycle
  and cancellation, and keeps the client stateless between turns.
- **Alternatives considered:** One long-lived socket with request multiplexing.
- **Advantages:** Simple, cancellable, testable without a server.
- **Disadvantages:** Reconnect cost per turn (negligible on localhost).
- **Impact:** `api/chatSocket.ts`, `chatStore`.

## ADR-0013 - Replace lucide-react with an inline SVG icon set

- **Date:** 2026-07-04 (M7)
- **Decision:** Do not depend on an icon package; ship a small inline SVG set.
- **Reason:** The resolved `lucide-react@1.x` was a version anomaly for this
  environment; avoiding the dependency removes supply-chain risk and shrinks the
  bundle.
- **Alternatives considered:** Pin a specific lucide version; use a different
  icon library.
- **Advantages:** Zero icon dependency, fully controlled, smaller bundle.
- **Disadvantages:** We maintain the icons ourselves (a handful).
- **Impact:** `components/icons.tsx`.

## ADR-0012 - Markdown rendering via react-markdown + rehype-highlight

- **Date:** 2026-07-04 (M7)
- **Decision:** Render assistant markdown with `react-markdown` + `remark-gfm` +
  `rehype-highlight`; override the code renderer to add a copy button.
- **Reason:** Safe (no `dangerouslySetInnerHTML`), GFM support, and CSS-class
  highlighting without a heavy syntax-highlighter component.
- **Alternatives considered:** `react-syntax-highlighter` (heavier), a custom
  markdown parser.
- **Advantages:** Safe, composable, lighter; copy button integrates cleanly.
- **Disadvantages:** Highlight bundle size (mitigated by vendor chunking).
- **Impact:** `components/chat/MarkdownMessage.tsx`, `CodeBlock.tsx`, build config.

## ADR-0011 - Electron owns the backend only in packaged builds; hide-to-tray

- **Date:** 2026-07-04 (M7)
- **Decision:** `BackendManager` spawns/health-checks/auto-restarts the backend
  in packaged builds; in dev the backend runs separately. Closing the window
  hides to the system tray instead of quitting.
- **Reason:** Avoid double-spawning during development; provide a desktop-native
  always-available assistant.
- **Alternatives considered:** Always spawn; quit on window close.
- **Advantages:** Clean dev workflow; resilient backend; native UX.
- **Disadvantages:** Tray/packaging paths are not exercised headlessly.
- **Impact:** `electron/main.ts`, `electron/backend.ts`, `electron/tray.ts`.

## ADR-0010 - Secure IPC bridge (`window.exo`)

- **Date:** 2026-07-04 (M7)
- **Decision:** Expose only a minimal, typed API to the renderer via a
  context-isolated preload; all privileged actions use explicit IPC channels.
- **Reason:** Security — the renderer must never get direct Node/Electron access.
- **Alternatives considered:** `nodeIntegration: true` (unsafe).
- **Advantages:** Strong renderer isolation; typed, auditable surface.
- **Disadvantages:** Every capability needs an explicit channel.
- **Impact:** `electron/preload.ts`, `types/electron.ts`, `main.ts` IPC handlers.

## ADR-0009 - Adopt project-management documents as source

- **Date:** 2026-07-04 (M6)
- **Decision:** Maintain CHANGELOG, ROADMAP, TODO, ARCHITECTURE, DECISIONS,
  KNOWN_ISSUES and PROJECT_STATUS as living files, updated every milestone.
- **Reason:** Keep documentation synchronized with code and provide an auditable
  project history.
- **Alternatives considered:** Rely on commit messages / external tracker.
- **Advantages:** Self-contained, versioned with the code, reviewable in diffs.
- **Disadvantages:** Requires discipline to keep current; some duplication.
- **Impact:** Process-wide; no runtime effect.

## ADR-0008 - Align package version with milestone numbering

- **Date:** 2026-07-04 (M6)
- **Decision:** Set the package version to `0.6.0` (minor = milestone).
- **Reason:** Make CHANGELOG/ROADMAP/status internally consistent with the code.
- **Alternatives considered:** Keep `0.1.0`; use dates.
- **Advantages:** Clear mapping between releases and milestones.
- **Disadvantages:** Retroactive version labels for M4/M5 in the changelog.
- **Impact:** `__version__` and `pyproject`; health payload reports the version.

## ADR-0007 - Monotonic `seq` key for message ordering

- **Date:** 2026-07-04 (M6)
- **Decision:** Add an autoincrement integer `seq` primary key to `Message` and
  order by it; keep string `id` as the external identifier.
- **Reason:** Wall-clock `created_at` collides under coarse OS timer resolution
  (~15 ms on Windows), making the chat context window nondeterministic.
- **Alternatives considered:** Higher-resolution timestamps (still collide);
  time-sortable UUIDs (complex); in-process counters (not restart-safe).
- **Advantages:** Correct, DB-native ordering; minimal code impact.
- **Disadvantages:** Message PK is now integer (internal change).
- **Impact:** `Message` model + conversation repository ordering.

## ADR-0006 - Tool safety model: permissions + sandbox + confirmation

- **Date:** 2026-07-04 (M6)
- **Decision:** Three independent safeguards — a permission policy (hard
  allow/deny by category), a filesystem sandbox (root confinement, traversal
  protection), and per-tool confirmation for sensitive actions. Deny-by-default
  for filesystem access and app launching.
- **Reason:** Local tools can touch the filesystem and spawn processes; safety
  must be layered and safe by default.
- **Alternatives considered:** Single global allow/deny; confirmation only.
- **Advantages:** Defense in depth; safe defaults; configurable.
- **Disadvantages:** Tools are inert until configured (roots/allow-lists).
- **Impact:** Tool framework and its configuration surface.

## ADR-0005 - Injectable OS backends for tools

- **Date:** 2026-07-04 (M6)
- **Decision:** Abstract clock, clipboard, URL opener, screenshotter and app
  launcher behind interfaces injected into tools.
- **Reason:** Determinism and testability without real OS side effects; keeps
  tools free of platform code.
- **Alternatives considered:** Direct OS calls inside tools.
- **Advantages:** Fully unit-testable; swappable per platform.
- **Disadvantages:** More indirection; default screenshot backend is a stub.
- **Impact:** `app/services/tools/backends.py` and every OS-facing tool.

## ADR-0004 - Provider created once in the app lifespan

- **Date:** 2026-07-04 (M5)
- **Decision:** Build the `AIProvider` at startup and store it on `app.state`;
  build a per-request `ChatService` bound to the DB session.
- **Reason:** Reuse HTTP connection pools; separate shared (stateless) provider
  from request-scoped session.
- **Alternatives considered:** Per-request provider construction.
- **Advantages:** Efficient connection reuse; clean shutdown via `aclose`.
- **Disadvantages:** Shared mutable app state.
- **Impact:** `main.py` lifespan, `deps.py`.

## ADR-0003 - Streaming persists the assistant reply only on completion

- **Date:** 2026-07-04 (M5)
- **Decision:** During WebSocket streaming, accumulate deltas and persist the
  assistant message once the stream finishes.
- **Reason:** Avoid partial replies in history if a stream is interrupted.
- **Alternatives considered:** Incremental persistence.
- **Advantages:** Consistent history; simpler recovery.
- **Disadvantages:** In-flight text isn't durable until completion.
- **Impact:** `ChatService.stream_message`.

## ADR-0002 - `ProviderFactory` with decorator-based auto-registration

- **Date:** 2026-07-04 (M4)
- **Decision:** Providers self-register via a decorator; the factory selects one
  from settings. Providers build themselves via `from_settings`.
- **Reason:** Open/Closed — add providers without editing the factory.
- **Alternatives considered:** Hard-coded factory switch; entry points.
- **Advantages:** Extensible; factory stays unchanged.
- **Disadvantages:** Registration relies on module import for discovery.
- **Impact:** `app/services/ai/`.

## ADR-0001 - HTTP providers over vendor SDKs

- **Date:** 2026-07-04 (M4)
- **Decision:** Implement OpenAI/Anthropic via `httpx` against their REST APIs
  rather than official SDKs, with an injectable client.
- **Reason:** Minimal dependencies, full control over requests/streaming,
  trivial mocking in tests.
- **Alternatives considered:** Official SDKs.
- **Advantages:** Light, testable, no vendor SDK churn.
- **Disadvantages:** We maintain request/SSE parsing ourselves.
- **Impact:** `app/services/ai/providers/`.
