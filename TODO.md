# TODO

Live engineering task list. Tasks move to **Completed** as they finish.
Priorities: High (blocks the next milestone or is a correctness/security risk),
Medium (important, not blocking), Low (nice-to-have / hygiene).

## High Priority

- **Plugin system (M8)** — `PluginManager`, manifest validation, capability
  scoping, and plugin-contributed tools/routes discovered at startup.
  Status: Not started · Priority: High · Milestone: M8
- **Chat tool-calling loop** — Let the model request tool execution mid-chat,
  stream `tool` events to the UI (indicators already built), and feed results
  back into the turn.
  Status: Not started · Priority: High · Milestone: M8

## Medium Priority

- **Database migrations (Alembic)** — Replace `create_all` with migrations
  before any schema change ships to existing databases.
  Status: Not started · Priority: Medium · Milestone: Tech debt
- **Test coverage tooling** — Add `pytest-cov` (backend) and Vitest coverage
  (frontend); set CI thresholds.
  Status: Not started · Priority: Medium · Milestone: Tech debt
- **End-to-end tests** — Playwright/Electron E2E for the packaged desktop flow
  (needs a display; not runnable headless here).
  Status: Not started · Priority: Medium · Milestone: M9
- **Screenshot capture backend** — Provide a real cross-platform capture backend
  (e.g. mss/Pillow) behind the existing `Screenshotter` abstraction.
  Status: Not started · Priority: Medium · Milestone: Future
- **Tray icon asset + real notifications wiring** — Ship a tray icon and connect
  in-app notifications to native ones where appropriate.
  Status: Not started · Priority: Medium · Milestone: M9

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

- **Desktop UI (M7)** — Full React chat interface: sidebar/history/search,
  streaming, markdown + syntax highlighting + copy, attachments + drag-drop,
  settings, theme switching, notifications, indicators, shortcuts, a11y.
  Status: Done · Priority: High · Milestone: M7
- **Frontend architecture (M7)** — Zustand stores, typed REST client, WebSocket
  streaming client, reusable components, inline SVG icons.
  Status: Done · Priority: High · Milestone: M7
- **Electron integration (M7)** — Backend process manager + auto-restart, secure
  IPC bridge, native notifications, system tray, window-state persistence.
  Status: Done · Priority: High · Milestone: M7
- **Frontend test suite (M7)** — Vitest + Testing Library (23 tests).
  Status: Done · Priority: High · Milestone: M7
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
