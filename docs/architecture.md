# EXO Architecture

## Overview

EXO is a local client-server desktop application:

- **Frontend:** Electron shell hosting a React + TypeScript + Tailwind renderer.
- **Backend:** FastAPI server on `localhost` exposing REST + WebSocket APIs.
- **Storage:** SQLite via SQLAlchemy (conversations, messages, profiles, preferences, events, actions).

## Backend layering

```
api/ (routers)  →  services/  →  repositories  →  models/ (SQLAlchemy)
                     │
                     ├── ai/       AIProvider abstraction + provider factory
                     ├── tools/    BaseTool interface + registry + built-in tools
                     └── plugins/  PluginManager (manifest-validated discovery)
```

Key principles:

- Routers never touch the database directly.
- All external AI models sit behind the `AIProvider` interface — no vendor lock-in.
- Every tool declares a Pydantic schema and a `requires_confirmation` flag.
- Destructive operations (delete/move files, terminal, system settings) are gated
  by a `ConfirmationGuard`: execution pauses until the client confirms explicitly.

## Frontend structure

- `electron/` — main + preload processes (contextIsolation on, sandbox on).
- `src/components/` — chat UI, sidebar, settings, markdown renderer.
- `src/stores/` — Zustand state (chat, settings, tools).
- `src/api/` — typed REST client and WebSocket streaming hook.

## Communication

- REST for CRUD (conversations, settings, tools, memory, health).
- WebSocket `/ws/chat` for token streaming, tool status events and confirmation prompts.

Further documents: `docs/ai-providers.md` (provider layer, Milestone 4),
`docs/chat.md` (chat pipeline: REST + WebSocket, Milestone 5). Planned:
`docs/api.md`, `docs/installation.md`, `docs/developer-guide.md` (Milestone 8).
