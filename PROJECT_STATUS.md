# EXO Project Status

Snapshot dashboard. Regenerated after every milestone.

**Generated:** 2026-07-04 · **Version:** 0.7.0

## Summary

| Field | Value |
|---|---|
| Current version | 0.7.0 |
| Current milestone | M7 - Desktop UI & Electron (completed) |
| Next milestone | M8 - Plugin system |
| Repository health | 🟢 Healthy |
| Overall completion | ~82% |

## Quality gates

| Gate | Status | Detail |
|---|---|---|
| Backend build | 🟢 Pass | App factory + lifespan import cleanly |
| Frontend build | 🟢 Pass | `vite build`, no warnings (vendor-chunked) |
| Electron compile | 🟢 Pass | `tsc -p electron` clean |
| Backend tests | 🟢 Pass | 77 passed (pytest) |
| Frontend tests | 🟢 Pass | 23 passed (vitest, 8 files) |
| Lint (ruff / eslint) | 🟢 Pass | backend + frontend clean |
| Format (black / prettier) | 🟢 Pass | backend + frontend clean |
| Type check (mypy --strict / tsc) | 🟢 Pass | 55 backend files + frontend, no issues |
| Coverage | ⚪ Not measured | no coverage tool configured (tracked in TODO) |

## Subsystem progress

| Subsystem | Progress | Notes |
|---|---|---|
| Backend core | 🟢 95% | Models, repositories, schemas, DB, config, logging |
| AI system | 🟢 90% | Interface, factory, Echo/OpenAI/Anthropic, streaming |
| Chat system | 🟢 85% | ChatService, memory/context, REST + WebSocket |
| Tool system | 🟢 90% | Framework + 13 tools + REST; screenshot backend pending |
| Plugin system | 🔴 0% | Not started (M8) |
| Frontend | 🟢 85% | Full chat UI, stores, clients, Electron; tool-calling loop pending |
| Documentation | 🟡 65% | Subsystem docs done; api/install/dev-guide pending |

## Milestones

| # | Milestone | Status |
|---|---|---|
| M1 | Foundation | ✅ Complete |
| M2 | Stack wiring | ✅ Complete |
| M3 | Backend core | ✅ Complete |
| M4 | AI provider architecture | ✅ Complete |
| M5 | Chat pipeline | ✅ Complete |
| M6 | Tool framework | ✅ Complete |
| M7 | Desktop UI & Electron integration | ✅ Complete |
| M8 | Plugin system | ⏳ Not started |
| M9 | Documentation & packaging | ⏳ Not started |

## Test breakdown (backend)

| Suite | Focus |
|---|---|
| `test_health` | Startup + health endpoint |
| `test_repositories` | Data-access layer |
| `test_ai_providers` | Provider layer (echo + mocked HTTP) |
| `test_chat` / `test_chat_api` | Chat service + REST/WebSocket |
| `test_tools_builtin` | Each built-in tool |
| `test_tools_framework` | Registry, permissions, sandbox, engine |
| `test_tools_api` | Tools REST (execute/confirm/deny/history) |

## Test breakdown (frontend, vitest)

| Suite | Focus |
|---|---|
| `api/client.test` | REST client success/error/network handling |
| `stores/chatStore.test` | Streaming send flow, empty input, error handling |
| `stores/settingsStore.test` | Theme + toggle state |
| `components/*` | Sidebar, MessageInput, SettingsModal, Notifications, MarkdownMessage (copy) |

## Notable risks / debt

- No authentication on the API surface (local-first). See KNOWN_ISSUES.
- No DB migrations (create_all). See ROADMAP → technical debt.
- Coverage not yet tracked.

See `ROADMAP.md`, `TODO.md`, `KNOWN_ISSUES.md` and `CHANGELOG.md` for detail.
