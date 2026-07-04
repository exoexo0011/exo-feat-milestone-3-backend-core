# EXO – AI Desktop Assistant

EXO is a modern, modular, production-grade desktop AI assistant.

- **Backend:** Python 3.12 · FastAPI · SQLAlchemy · SQLite · Pydantic
- **Frontend:** Electron · React · TypeScript · TailwindCSS
- **Communication:** REST API + WebSockets (streaming)

## Quick Start

```bash
git clone https://gitlab.com/exo-group9325627/exo.git
cd exo
./scripts/bootstrap.sh        # installs everything and starts backend + frontend
```

Backend: http://127.0.0.1:8000 (docs at `/docs`) · Frontend dev server: http://127.0.0.1:5173

## Repository Layout

```
backend/     FastAPI application (layered: api → services → repositories → models)
frontend/    Electron + React + TypeScript + Tailwind UI
database/    SQLite database files (gitignored)
plugins/     Drop-in plugin directory (discovered at startup)
tests/       Pytest suite
docs/        Architecture, API, install and developer documentation
scripts/     Bootstrap and development scripts
```

## Development

| Task | Command |
|---|---|
| Backend dev server | `cd backend && uvicorn app.main:app --reload` |
| Frontend dev (web) | `cd frontend && npm run dev` |
| Frontend dev (Electron) | `cd frontend && npm run electron:dev` |
| Python lint/format | `ruff check backend tests && black --check backend tests` |
| Python types | `mypy backend/app` |
| Frontend lint | `cd frontend && npm run lint && npm run format:check` |
| Tests | `pytest` |

## Packaging (desktop installers)

```bash
./scripts/package.sh        # Linux/macOS   (Windows: .\scripts\package.ps1)
```

Builds a self-contained desktop app (backend bundled via PyInstaller, packaged
with electron-builder) into `frontend/release/`. See
[docs/installation.md](docs/installation.md).

## Documentation

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | High-level architecture |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Living, detailed architecture |
| [docs/api.md](docs/api.md) | REST + WebSocket API reference |
| [docs/installation.md](docs/installation.md) | Install & configuration |
| [docs/developer-guide.md](docs/developer-guide.md) | Contributing & extending |
| [docs/migration-guide.md](docs/migration-guide.md) | Upgrade notes |
| [docs/ai-providers.md](docs/ai-providers.md) · [chat.md](docs/chat.md) · [tools.md](docs/tools.md) · [plugins.md](docs/plugins.md) | Subsystem guides |

## License

Proprietary – all rights reserved (Phase 1).
