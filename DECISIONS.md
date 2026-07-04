# Architecture Decision Record (ADR)

Chronological record of significant technical decisions. Newest first.

---

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
