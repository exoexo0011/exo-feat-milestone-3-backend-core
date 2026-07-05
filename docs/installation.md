# Installation & Configuration

## Prerequisites

- **Python 3.12** (the backend targets 3.12; other versions are unsupported).
- **Node.js 20+** and npm (frontend + Electron).
- Optional: **Docker** (containerised backend + web frontend).

## Quick start (developers)

```bash
git clone https://github.com/exoexo0011/exo-feat-milestone-3-backend-core.git
cd exo-feat-milestone-3-backend-core
./scripts/bootstrap.sh          # Linux/macOS: venv + deps + dev servers
# Windows PowerShell:
#   .\scripts\bootstrap.ps1
```

- Backend: <http://127.0.0.1:8000> (API docs at `/docs`)
- Frontend dev server: <http://127.0.0.1:5173>

`bootstrap.sh --setup` (or `bootstrap.ps1 -SetupOnly`) installs dependencies
without starting the servers.

## Manual setup

Backend:

```bash
python -m venv .venv && . .venv/bin/activate    # Windows: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env             # optional; adjust as needed
cd backend && uvicorn app.main:app --reload
```

Frontend (web dev server, proxies `/api` and `/ws` to the backend):

```bash
cd frontend
npm install
npm run dev
```

Frontend as an Electron app in development:

```bash
cd frontend
npm run electron:dev
```

## Configuration

Settings are resolved from environment variables prefixed `EXO_` (or a
`backend/.env` file). List-valued variables use JSON (e.g.
`EXO_CORS_ORIGINS='["http://localhost:5173"]'`).

### Core

| Variable | Default | Description |
|---|---|---|
| `EXO_ENV` | `development` | `development` / `test` / `production` |
| `EXO_HOST` | `127.0.0.1` | Bind host |
| `EXO_PORT` | `8000` | Bind port |
| `EXO_DB_PATH` | `../database/exo.db` | SQLite database path |
| `EXO_LOG_LEVEL` | `INFO` | Logging level |
| `EXO_LOG_DIR` | `../logs` | Log directory |
| `EXO_LOG_JSON` | `false` | JSON log format |
| `EXO_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |

### AI provider

| Variable | Default | Description |
|---|---|---|
| `EXO_AI_PROVIDER` | `echo` | `echo` / `openai` / `anthropic` |
| `EXO_AI_MODEL` | (provider default) | Optional model override |
| `EXO_AI_TEMPERATURE` | `0.7` | |
| `EXO_AI_MAX_TOKENS` | `1024` | |
| `EXO_AI_REQUEST_TIMEOUT` | `60` | Seconds |
| `OPENAI_API_KEY` / `EXO_OPENAI_API_KEY` | — | OpenAI key |
| `EXO_OPENAI_BASE_URL` | `https://api.openai.com/v1` | |
| `ANTHROPIC_API_KEY` / `EXO_ANTHROPIC_API_KEY` | — | Anthropic key |
| `EXO_ANTHROPIC_BASE_URL` | `https://api.anthropic.com/v1` | |
| `EXO_ANTHROPIC_VERSION` | `2023-06-01` | |

### Chat

| Variable | Default | Description |
|---|---|---|
| `EXO_CHAT_SYSTEM_PROMPT` | "You are EXO, …" | Leading system prompt |
| `EXO_CHAT_MAX_CONTEXT_MESSAGES` | `20` | Recency window size |

### Tools

| Variable | Default | Description |
|---|---|---|
| `EXO_TOOL_FS_ALLOWED_ROOTS` | `[]` | Filesystem sandbox roots (empty = FS denied) |
| `EXO_TOOL_MAX_FILE_BYTES` | `1048576` | Max read/write size |
| `EXO_TOOL_ALLOWED_APPS` | `[]` | Launcher allow-list (empty = launch denied) |
| `EXO_TOOL_DENIED_PERMISSIONS` | `[]` | Hard-disabled capability categories |

### Plugins

| Variable | Default | Description |
|---|---|---|
| `EXO_PLUGINS_ENABLED` | `true` | Master switch |
| `EXO_PLUGINS_DIR` | `../plugins` | Plugin discovery directory |

## Docker (backend + web frontend)

```bash
docker compose up --build
```

- Backend: <http://127.0.0.1:8000>
- Web frontend: <http://127.0.0.1:5173>

The compose stack runs the browser-based web build; the Electron desktop app is
packaged separately (below).

## Desktop installers (end users)

Packaged installers bundle the backend (as a self-contained executable) with the
Electron app, so end users do not need Python or Node.

Build locally on the target OS:

```bash
# Linux/macOS
./scripts/package.sh
# Windows
.\scripts\package.ps1
```

This runs a two-step build — PyInstaller bundles the backend, then
electron-builder produces the platform installer in `frontend/release/`
(Windows NSIS, macOS dmg, Linux AppImage). See
[developer-guide.md](./developer-guide.md) for details and the release pipeline.

> Installers are OS-specific: build each platform's installer on that platform
> (or a matching CI runner). Code signing is left to CI environment secrets.
