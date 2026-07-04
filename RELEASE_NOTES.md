# EXO Release Notes

User-facing highlights per release. See [CHANGELOG.md](./CHANGELOG.md) for the
complete, categorised change list and [docs/migration-guide.md](./docs/migration-guide.md)
for upgrade steps.

## 0.9.0 — Documentation & Packaging

- **Desktop installers.** EXO can now be packaged into a standalone desktop app:
  the Python backend is bundled with PyInstaller and shipped inside the Electron
  app (Windows NSIS, macOS dmg, Linux AppImage) — end users need neither Python
  nor Node. Build with `scripts/package.sh` / `scripts/package.ps1`.
- **Complete documentation.** New API reference, installation & configuration
  guide, developer guide, and migration guide.
- **End-to-end tests.** A Playwright smoke suite exercises the full stack
  (renderer → backend, echo provider) in CI.
- **Release pipeline.** CI now runs frontend tests and E2E on every push and
  builds release artifacts on tags.
- **Reliability fix.** The chat WebSocket now handles a client disconnecting
  mid-stream cleanly instead of logging an unhandled error.

## 0.8.0 — Plugin Framework

- A complete plugin system: drop a folder with a `plugin.json` into `plugins/`
  to add tools, commands, API routes, UI panels, and event handlers.
- Permission-scoped, version-checked, dependency-ordered, and failure-isolated —
  a broken plugin can't take down the app.
- An in-process event bus (chat/tool/system/plugin events) and a reference
  plugin (`hello_exo`).

## 0.7.0 — Desktop UI & Electron

- A full ChatGPT-style desktop interface: conversation sidebar with search,
  streaming replies, markdown + syntax highlighting with copy buttons, file
  attachments and drag-and-drop, settings with light/dark/system themes,
  notifications, keyboard shortcuts, and accessibility.
- Electron integration: managed backend process with auto-restart, secure IPC,
  native notifications, system tray, and window-state persistence.

## 0.6.0 — Tool Framework

- A sandboxed tool system with a permission policy and confirmation flow, plus 13
  built-in tools (calculator, time, clipboard, open URL, file read/write, list,
  search, create/move/delete, screenshot, launch app).

## 0.5.0 — Chat Pipeline

- Conversations, streaming chat over REST and WebSocket, and conversation context
  management.

## 0.4.0 — AI Providers

- A vendor-agnostic provider layer with Echo, OpenAI, and Anthropic providers and
  streaming support.
