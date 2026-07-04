# Migration Guide

Upgrade notes between EXO versions. EXO is pre-1.0 (each milestone is a minor
release); breaking changes are called out explicitly here. The full change list
lives in [CHANGELOG.md](../CHANGELOG.md).

## General notes

- **Database:** the schema is created on startup via `create_all`; there are no
  Alembic migrations yet. During Phase 1, schema changes are applied by
  recreating the local SQLite database (delete `database/exo.db`). Do not rely on
  in-place schema upgrades until migrations land.
- **Configuration:** all settings are `EXO_*` environment variables (or
  `backend/.env`). New settings ship with safe defaults, so upgrades do not
  require configuration changes unless you opt in to a feature.

## 0.8.0 → 0.9.0

No breaking changes. Additive only:

- **Packaging:** desktop installers via PyInstaller + electron-builder
  (`scripts/package.*`). Building installers adds `pyinstaller` (backend dev
  dependency) and `electron-builder` + `@playwright/test` (frontend dev
  dependencies) — run `pip install -r backend/requirements-dev.txt` and
  `npm install` to pick them up.
- **Packaged data location:** in a packaged desktop build the backend now writes
  its database and logs under the OS per-user data directory (`userData`) rather
  than next to the executable. Development runs are unchanged.
- **Docs:** new `api.md`, `installation.md`, `developer-guide.md`, this guide,
  and `RELEASE_NOTES.md`.

No action required for existing dev setups beyond reinstalling dependencies.

## 0.5.0 → 0.6.0 (breaking: internal data model)

- **`Message` primary key changed.** The `messages` table gained a monotonic
  autoincrement integer primary key (`seq`) for reliable ordering; the public
  string `id` remains as a unique, indexed identifier. This is an internal change
  with **no REST/WebSocket API impact** (responses still expose `id`).
  - **Action:** because there are no migrations yet, recreate the local database
    (`database/exo.db`) when upgrading across this boundary.
- New tool settings were introduced (`EXO_TOOL_FS_ALLOWED_ROOTS`,
  `EXO_TOOL_MAX_FILE_BYTES`, `EXO_TOOL_ALLOWED_APPS`,
  `EXO_TOOL_DENIED_PERMISSIONS`). Filesystem tools are **denied by default**
  until you configure sandbox roots.

## 0.4.0 → 0.5.0

- Additive: chat pipeline (`/api/chat`, `/ws/chat`) and settings
  `EXO_CHAT_SYSTEM_PROMPT`, `EXO_CHAT_MAX_CONTEXT_MESSAGES`. No action required.

## Earlier

- **0.4.0** introduced the AI provider layer and `EXO_AI_*` settings plus
  `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`. The default provider is `echo`
  (no key, no network), so no configuration is required to run.

## Settings introduced by version

| Version | New settings |
|---|---|
| 0.4.0 | `EXO_AI_PROVIDER`, `EXO_AI_MODEL`, `EXO_AI_TEMPERATURE`, `EXO_AI_MAX_TOKENS`, `EXO_AI_REQUEST_TIMEOUT`, OpenAI/Anthropic keys + base URLs |
| 0.5.0 | `EXO_CHAT_SYSTEM_PROMPT`, `EXO_CHAT_MAX_CONTEXT_MESSAGES` |
| 0.6.0 | `EXO_TOOL_FS_ALLOWED_ROOTS`, `EXO_TOOL_MAX_FILE_BYTES`, `EXO_TOOL_ALLOWED_APPS`, `EXO_TOOL_DENIED_PERMISSIONS` |
| 0.8.0 | `EXO_PLUGINS_ENABLED`, `EXO_PLUGINS_DIR` |
