# Known Issues

Tracks bugs, limitations and workarounds. Resolved items move to **Resolved**.
Severity: Critical / High / Medium / Low.

## Open

### ISSUE-005 - No authentication on REST/WebSocket surface
- **Severity:** High (only when exposed beyond localhost)
- **Status:** Open (by design for local-first Phase 1)
- **Description:** All endpoints, including `/api/tools/*` (filesystem, process
  launch) and `/ws/chat`, are unauthenticated.
- **Workaround:** Bind to `127.0.0.1`; rely on the permission policy, sandbox
  and confirmation flow. Do not expose the backend on `0.0.0.0` in production.
- **Planned fix:** Add an auth layer before any remote mode (long-term goal).

### ISSUE-004 - `screenshot` tool has no default capture backend
- **Severity:** Low
- **Status:** Open
- **Description:** The default `Screenshotter` returns "unavailable"; the tool
  exists and is validated/sandboxed but cannot capture until a backend is
  injected.
- **Workaround:** Inject a platform capture backend.
- **Planned fix:** Add an mss/Pillow-based backend (future milestone).

### ISSUE-003 - No database migrations
- **Severity:** Medium
- **Status:** Open
- **Description:** Schema is created via `create_all`; changing the schema on an
  existing database has no migration path.
- **Workaround:** Recreate the local database in Phase 1.
- **Planned fix:** Introduce Alembic before schema changes ship.

### ISSUE-002 - Test coverage not measured
- **Severity:** Low
- **Status:** Open
- **Description:** No coverage tooling; the reported coverage is unknown.
- **Workaround:** N/A (77 tests pass across unit + integration).
- **Planned fix:** Add `pytest-cov` and a CI threshold.

### ISSUE-001 - `db_path` resolves relative to the working directory
- **Severity:** Low
- **Status:** Open
- **Description:** The default `db_path` (`../database/exo.db`) depends on the
  process CWD; launching from an unexpected directory changes the DB location.
- **Workaround:** Run from `backend/` or set `EXO_DB_PATH` explicitly.
- **Planned fix:** Resolve relative to a well-known base directory.

## Resolved

### ISSUE-R002 - Nondeterministic message ordering under coarse timers
- **Severity:** High · **Status:** Resolved in 0.6.0 (M6)
- **Description:** `list_recent_messages` ordered by `created_at`, which collides
  when messages are inserted within one OS timer tick (~15 ms on Windows),
  producing a wrong/unstable context window.
- **Fix:** Added a monotonic autoincrement `seq` key to `Message`; ordering now
  uses `seq`.

### ISSUE-R001 - Frontend `MODULE_TYPELESS_PACKAGE_JSON` build warning
- **Severity:** Low · **Status:** Resolved in 0.6.0 (M6)
- **Description:** Node warned that ESM `postcss.config.js` was loaded from a
  typeless package.
- **Fix:** Renamed PostCSS/Tailwind configs to `.mjs` (Electron main stays
  CommonJS, so `type: module` was not set on `package.json`).
