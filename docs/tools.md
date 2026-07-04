# Tool Framework

Milestone 6 adds the capability layer: schema-validated **tools** the assistant
can invoke, governed by a permission policy, a filesystem sandbox and an
explicit confirmation flow, with every invocation recorded in an audit trail.

## Components

```
app/services/tools/
├── base.py         BaseTool, ToolContext, ToolResult, ToolStatus, Permission, errors
├── registry.py     ToolRegistry (name -> tool instance)
├── permissions.py  PermissionPolicy (hard allow/deny by category)
├── sandbox.py      FileSandbox (root confinement + traversal protection)
├── backends.py     Clock, ClipboardBackend, UrlOpener, Screenshotter, AppLauncher
├── engine.py       ToolExecutionEngine (validate -> authorise -> confirm -> run -> audit)
└── builtins/       the 13 built-in tools + build_builtin_tools discovery
```

### BaseTool

A tool declares a unique `name`, a `description`, a Pydantic `params_model`, the
set of `permissions` it needs, and whether it `requires_confirmation`. It
implements `async run(params, context) -> dict` and returns JSON-serialisable
output or raises a `ToolError`. `spec()` exposes a machine-readable description
(name, permissions, JSON-schema of parameters) for AI tool-calling and UIs.

### Execution engine

`ToolExecutionEngine.execute(name, arguments, context)` performs, in order:

1. **Resolve** the tool (unknown name raises `ToolNotFoundError`).
2. **Validate** arguments against `params_model` (failure -> `FAILED` result).
3. **Authorise** via the permission policy (denied -> `DENIED` result).
4. **Confirm**: if the tool requires confirmation and the context is not
   confirmed, a pending `AssistantAction` is recorded and a
   `CONFIRMATION_REQUIRED` result is returned. Resume with
   `confirm(action_id)` or reject with `deny(action_id)`.
5. **Run** the tool, translating any error into a `FAILED` result.
6. **Audit**: record the invocation in the `assistant_actions` table
   (`PENDING -> CONFIRMED -> COMPLETED/FAILED/DENIED`). History is optional -
   without an `EventRepository` the engine still runs (used by unit tests).

`ToolResult` is the uniform outcome: `tool`, `status`, `output`, `error`,
`action_id`.

### Permissions, confirmation and sandbox

- **Permissions** are coarse capability categories (`filesystem_read`,
  `filesystem_write`, `network`, `clipboard`, `system`, `process`). The policy
  is a hard gate configured by `tool_denied_permissions`; a denied category
  blocks the tool regardless of confirmation.
- **Confirmation** is a per-tool flag for sensitive/irreversible actions. It is
  orthogonal to permissions: a permitted-but-sensitive action still pauses for
  explicit user approval.
- **The sandbox** confines every filesystem path to configured root
  directories, resolving symlinks and `..` so traversal cannot escape. With no
  roots configured, filesystem access is denied - a safe default.

## Configuration

| Setting | Env var | Default | Effect |
|---|---|---|---|
| `tool_fs_allowed_roots` | `EXO_TOOL_FS_ALLOWED_ROOTS` | `[]` | Filesystem sandbox roots (empty = FS denied) |
| `tool_max_file_bytes` | `EXO_TOOL_MAX_FILE_BYTES` | `1048576` | Max read/write size |
| `tool_allowed_apps` | `EXO_TOOL_ALLOWED_APPS` | `[]` | Launcher allow-list (empty = launch denied) |
| `tool_denied_permissions` | `EXO_TOOL_DENIED_PERMISSIONS` | `[]` | Hard-disabled categories |

List-valued env vars are JSON (e.g. `EXO_TOOL_FS_ALLOWED_ROOTS='["C:/Users/me/exo"]'`).

## Built-in tools

| Tool | Permissions | Confirm | Notes |
|---|---|---|---|
| `calculator` | – | no | Safe AST arithmetic (no `eval`) |
| `current_time` | – | no | Optional IANA timezone |
| `clipboard` | clipboard | no | `action: read/write` |
| `open_url` | network | yes | http/https/mailto only |
| `read_file` | filesystem_read | no | UTF-8, sandboxed, size-capped |
| `write_file` | filesystem_write | yes | Sandboxed, creates parents |
| `list_directory` | filesystem_read | no | |
| `search_files` | filesystem_read | no | Recursive glob |
| `create_folder` | filesystem_write | no | |
| `move_files` | filesystem_write | yes | Refuses to overwrite |
| `delete_files` | filesystem_write | yes | `recursive` for non-empty dirs |
| `screenshot` | system, filesystem_write | yes | Requires a capture backend |
| `launch_application` | process | yes | Allow-listed apps only |

OS-facing tools depend on injectable backends (`backends.py`), so they are fully
unit-testable with in-memory/recording fakes and deterministic clocks. The
default screenshot backend reports "unavailable" until a platform capture
backend is injected.

## REST API

Under `/api/tools` (unauthenticated, like the rest of the local-first backend -
see the security note below):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/tools` | List tools and their parameter schemas |
| `POST` | `/tools/{name}/execute` | Execute (`{arguments, confirm, conversation_id}`) |
| `POST` | `/tools/actions/{id}/confirm` | Run a pending (confirmation-required) action |
| `POST` | `/tools/actions/{id}/deny` | Reject a pending action |
| `GET` | `/tools/history` | Recent invocations from the audit trail |

**Security note:** these endpoints expose local capabilities (filesystem,
process launch). They rely on the permission policy, sandbox and confirmation
flow for safety and must not be exposed beyond localhost without authentication.

## Testing

- `tests/test_tools_builtin.py` - each built-in tool with injected backends and
  a temporary sandbox.
- `tests/test_tools_framework.py` - registry, permission policy, sandbox
  traversal, and the engine (validation, denial, confirmation and deny flows,
  history recording).
- `tests/test_tools_api.py` - REST integration including the confirm/deny flow.
