# Developer Guide

How to work on EXO: architecture, standards, the quality gate, and how to extend
the system. See also [architecture.md](./architecture.md) and the subsystem docs.

## Project layout

```
backend/            FastAPI app (api -> services -> repositories -> models)
  app/api/          routers + dependency injection (deps.py)
  app/services/     ai/ (providers), chat, memory, tools/, plugins/, eventbus
  app/repositories/ data access (SQLAlchemy)
  app/models/       ORM models
  app/schemas/      Pydantic request/response models
  packaging/        PyInstaller entry + spec
frontend/           Electron + React + TypeScript + Tailwind
  src/              renderer (components, stores, api, hooks)
  electron/         main + preload + backend manager + tray + window state
  e2e/              Playwright end-to-end tests
plugins/            drop-in plugins (each a folder with plugin.json)
tests/              backend pytest suite
docs/               documentation (this folder)
scripts/            bootstrap + packaging scripts
```

## Architecture principles

- **Layered backend:** routers never touch the database directly; they depend on
  services/repositories via `app/api/deps.py`.
- **No vendor lock-in:** all models sit behind the `AIProvider` interface.
- **Safety by construction:** tools declare permissions + a confirmation flag and
  run inside a filesystem sandbox; plugins are permission-scoped and
  failure-isolated.
- **Typed throughout:** `mypy --strict` on the backend, `strict` TypeScript on
  the frontend.

## Coding standards

- **Python:** Ruff (lint + import order), Black (format, 100 cols), mypy strict.
  Domain errors subclass `ExoError`; keep HTTP concerns in the API layer.
- **TypeScript:** ESLint (`--max-warnings 0`) + Prettier; no `any`; components
  small and accessible (ARIA, keyboard).
- Write tests for new behaviour; keep functions focused (SOLID).

## The quality gate

Run all of these before committing (they mirror CI):

```bash
# Backend
ruff check backend tests
black --check backend tests
mypy backend/app
pytest

# Frontend (from frontend/)
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
npm run electron:compile

# End-to-end (starts backend + dev server automatically)
npm run test:e2e
```

## Extending EXO

### Add an AI provider

1. Create `backend/app/services/ai/providers/<name>.py`.
2. Subclass `AIProvider` (or `HttpChatProvider` for HTTP APIs), set a unique
   `name`, implement `from_settings`, `generate`, `stream`.
3. Decorate with `@ProviderFactory.register` and import it in
   `providers/__init__.py`. See [ai-providers.md](./ai-providers.md).

### Add a built-in tool

1. Subclass `BaseTool[Params]` with a Pydantic `params_model`, `permissions`,
   and (if destructive) `requires_confirmation = True`.
2. Register it in `services/tools/builtins/__init__.py`
   (`build_builtin_tools`). See [tools.md](./tools.md).

### Write a plugin

Create a folder under `plugins/` with a `plugin.json` and a `register(context)`
entry point. Use the SDK (`app.services.plugins.sdk`) to register tools,
commands, routes, event handlers and UI contributions. See
[plugins.md](./plugins.md); `plugins/hello_exo/` is a complete example.

## Testing

- **Backend:** `pytest` (unit + integration via FastAPI `TestClient`). Use the
  shared `db_session` fixture (in-memory SQLite) for repository/service tests.
- **Frontend:** Vitest + Testing Library (`npm run test`). Stores and the API
  client are unit-tested; components use accessible queries.
- **E2E:** Playwright (`npm run test:e2e`) drives a headless browser against the
  dev server + a live backend running the deterministic `echo` provider.

## Packaging & release

Packaging is a two-step build (see `scripts/package.*`):

1. **PyInstaller** bundles the backend into `backend/packaging/dist/exo-backend/`
   (spec: `backend/packaging/exo-backend.spec`).
2. **electron-builder** (`frontend/electron-builder.yml`) packages the renderer +
   Electron shell and ships the backend bundle and the `plugins/` directory as
   extra resources, producing an installer in `frontend/release/`.

At runtime the Electron main process (`electron/backend.ts`) spawns the bundled
`exo-backend` executable in packaged builds (pointing `EXO_DB_PATH`/`EXO_LOG_DIR`
at the per-user `userData` directory), and uses your local `python -m uvicorn`
in development.

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs lint, tests
(backend + frontend), build, and E2E on every push, and a tag-triggered
`release` job builds artifacts.

## Contribution workflow

1. Branch from `main`; keep changes focused.
2. Make the change with tests + docs.
3. Run the full quality gate (above) — everything must pass.
4. Update `CHANGELOG.md` and any affected docs.
5. Open a merge request; CI must be green.

## License

Proprietary — all rights reserved (Phase 1).
