# EXO Project Status

Snapshot dashboard. Regenerated after every milestone.

**Generated:** 2026-07-04 · **Version:** 0.6.0

## Summary

| Field | Value |
|---|---|
| Current version | 0.6.0 |
| Current milestone | M6 - Tool Framework (completed) |
| Next milestone | M7 - Frontend & Electron lifecycle |
| Repository health | 🟢 Healthy |
| Overall completion | ~68% |

## Quality gates

| Gate | Status | Detail |
|---|---|---|
| Backend build | 🟢 Pass | App factory + lifespan import cleanly |
| Frontend build | 🟢 Pass | `vite build`, no warnings |
| Unit + integration tests | 🟢 Pass | 77 passed (backend, pytest) |
| Lint (ruff) | 🟢 Pass | `backend` + `tests` clean |
| Format (black / prettier) | 🟢 Pass | backend + frontend clean |
| Type check (mypy --strict) | 🟢 Pass | 55 source files, no issues |
| Frontend typecheck (tsc) | 🟢 Pass | no errors |
| Coverage | ⚪ Not measured | no coverage tool configured (tracked in TODO) |

## Subsystem progress

| Subsystem | Progress | Notes |
|---|---|---|
| Backend core | 🟢 95% | Models, repositories, schemas, DB, config, logging |
| AI system | 🟢 90% | Interface, factory, Echo/OpenAI/Anthropic, streaming |
| Chat system | 🟢 85% | ChatService, memory/context, REST + WebSocket |
| Tool system | 🟢 90% | Framework + 13 tools + REST; screenshot backend pending |
| Plugin system | 🔴 0% | Not started (M8) |
| Frontend | 🟠 10% | Skeleton shell only; real UI in M7 |
| Documentation | 🟡 60% | Subsystem docs done; api/install/dev-guide pending |

## Milestones

| # | Milestone | Status |
|---|---|---|
| M1 | Foundation | ✅ Complete |
| M2 | Stack wiring | ✅ Complete |
| M3 | Backend core | ✅ Complete |
| M4 | AI provider architecture | ✅ Complete |
| M5 | Chat pipeline | ✅ Complete |
| M6 | Tool framework | ✅ Complete |
| M7 | Frontend & Electron lifecycle | ⏳ Not started |
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

## Notable risks / debt

- No authentication on the API surface (local-first). See KNOWN_ISSUES.
- No DB migrations (create_all). See ROADMAP → technical debt.
- Coverage not yet tracked.

See `ROADMAP.md`, `TODO.md`, `KNOWN_ISSUES.md` and `CHANGELOG.md` for detail.
