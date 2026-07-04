# Architecture Decision Record (ADR)

Chronological record of significant technical decisions. Newest first.

---

## ADR-0009 - Adopt project-management documents as source

- **Date:** 2026-07-04 (M6)
- **Decision:** Maintain CHANGELOG, ROADMAP, TODO, ARCHITECTURE, DECISIONS,
  KNOWN_ISSUES and PROJECT_STATUS as living files, updated every milestone.
- **Reason:** Keep documentation synchronized with code and provide an auditable
  project history.
- **Alternatives considered:** Rely on commit messages / external tracker.
- **Advantages:** Self-contained, versioned with the code, reviewable in diffs.
- **Disadvantages:** Requires discipline to keep current; some duplication.
- **Impact:** Process-wide; no runtime effect.

## ADR-0008 - Align package version with milestone numbering

- **Date:** 2026-07-04 (M6)
- **Decision:** Set the package version to `0.6.0` (minor = milestone).
- **Reason:** Make CHANGELOG/ROADMAP/status internally consistent with the code.
- **Alternatives considered:** Keep `0.1.0`; use dates.
- **Advantages:** Clear mapping between releases and milestones.
- **Disadvantages:** Retroactive version labels for M4/M5 in the changelog.
- **Impact:** `__version__` and `pyproject`; health payload reports the version.

## ADR-0007 - Monotonic `seq` key for message ordering

- **Date:** 2026-07-04 (M6)
- **Decision:** Add an autoincrement integer `seq` primary key to `Message` and
  order by it; keep string `id` as the external identifier.
- **Reason:** Wall-clock `created_at` collides under coarse OS timer resolution
  (~15 ms on Windows), making the chat context window nondeterministic.
- **Alternatives considered:** Higher-resolution timestamps (still collide);
  time-sortable UUIDs (complex); in-process counters (not restart-safe).
- **Advantages:** Correct, DB-native ordering; minimal code impact.
- **Disadvantages:** Message PK is now integer (internal change).
- **Impact:** `Message` model + conversation repository ordering.

## ADR-0006 - Tool safety model: permissions + sandbox + confirmation

- **Date:** 2026-07-04 (M6)
- **Decision:** Three independent safeguards — a permission policy (hard
  allow/deny by category), a filesystem sandbox (root confinement, traversal
  protection), and per-tool confirmation for sensitive actions. Deny-by-default
  for filesystem access and app launching.
- **Reason:** Local tools can touch the filesystem and spawn processes; safety
  must be layered and safe by default.
- **Alternatives considered:** Single global allow/deny; confirmation only.
- **Advantages:** Defense in depth; safe defaults; configurable.
- **Disadvantages:** Tools are inert until configured (roots/allow-lists).
- **Impact:** Tool framework and its configuration surface.

## ADR-0005 - Injectable OS backends for tools

- **Date:** 2026-07-04 (M6)
- **Decision:** Abstract clock, clipboard, URL opener, screenshotter and app
  launcher behind interfaces injected into tools.
- **Reason:** Determinism and testability without real OS side effects; keeps
  tools free of platform code.
- **Alternatives considered:** Direct OS calls inside tools.
- **Advantages:** Fully unit-testable; swappable per platform.
- **Disadvantages:** More indirection; default screenshot backend is a stub.
- **Impact:** `app/services/tools/backends.py` and every OS-facing tool.

## ADR-0004 - Provider created once in the app lifespan

- **Date:** 2026-07-04 (M5)
- **Decision:** Build the `AIProvider` at startup and store it on `app.state`;
  build a per-request `ChatService` bound to the DB session.
- **Reason:** Reuse HTTP connection pools; separate shared (stateless) provider
  from request-scoped session.
- **Alternatives considered:** Per-request provider construction.
- **Advantages:** Efficient connection reuse; clean shutdown via `aclose`.
- **Disadvantages:** Shared mutable app state.
- **Impact:** `main.py` lifespan, `deps.py`.

## ADR-0003 - Streaming persists the assistant reply only on completion

- **Date:** 2026-07-04 (M5)
- **Decision:** During WebSocket streaming, accumulate deltas and persist the
  assistant message once the stream finishes.
- **Reason:** Avoid partial replies in history if a stream is interrupted.
- **Alternatives considered:** Incremental persistence.
- **Advantages:** Consistent history; simpler recovery.
- **Disadvantages:** In-flight text isn't durable until completion.
- **Impact:** `ChatService.stream_message`.

## ADR-0002 - `ProviderFactory` with decorator-based auto-registration

- **Date:** 2026-07-04 (M4)
- **Decision:** Providers self-register via a decorator; the factory selects one
  from settings. Providers build themselves via `from_settings`.
- **Reason:** Open/Closed — add providers without editing the factory.
- **Alternatives considered:** Hard-coded factory switch; entry points.
- **Advantages:** Extensible; factory stays unchanged.
- **Disadvantages:** Registration relies on module import for discovery.
- **Impact:** `app/services/ai/`.

## ADR-0001 - HTTP providers over vendor SDKs

- **Date:** 2026-07-04 (M4)
- **Decision:** Implement OpenAI/Anthropic via `httpx` against their REST APIs
  rather than official SDKs, with an injectable client.
- **Reason:** Minimal dependencies, full control over requests/streaming,
  trivial mocking in tests.
- **Alternatives considered:** Official SDKs.
- **Advantages:** Light, testable, no vendor SDK churn.
- **Disadvantages:** We maintain request/SSE parsing ourselves.
- **Impact:** `app/services/ai/providers/`.
