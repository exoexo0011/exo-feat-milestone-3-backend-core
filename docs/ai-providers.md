# AI Providers

EXO talks to language models through a single vendor-agnostic interface,
`AIProvider`. Application code (services, the chat pipeline) depends only on
this interface, never on a concrete vendor client, so models can be swapped
through configuration alone.

## Layout

```
backend/app/services/ai/
├── base.py              # ChatMessage, CompletionResult, StreamChunk, Usage, AIProvider
├── factory.py           # ProviderFactory (registry + create-from-settings)
└── providers/
    ├── _httpbase.py     # HttpChatProvider: httpx lifecycle + JSON/SSE helpers
    ├── echo.py          # EchoProvider  (no key, no network)
    ├── openai.py        # OpenAIProvider
    └── anthropic.py     # AnthropicProvider
```

## The interface

Every provider implements `AIProvider`:

- `from_settings(settings) -> AIProvider` — build the provider from `Settings`.
- `generate(messages, *, model=None, temperature=None, max_tokens=None) -> CompletionResult`
  — a single-shot completion.
- `stream(messages, *, ...) -> AsyncIterator[StreamChunk]` — token streaming.
- `aclose()` — release resources (HTTP providers close their client here).

Value types are plain, immutable dataclasses:

- `ChatMessage(role, content)` where `role` is `"system" | "user" | "assistant"`.
- `CompletionResult(content, model, provider, finish_reason, usage)`.
- `StreamChunk(delta, finish_reason)` — `finish_reason` is set only on the last chunk.
- `Usage(prompt_tokens, completion_tokens, total_tokens)`.

## Configuration

Providers are selected and configured entirely through `Settings`
(environment variables prefixed `EXO_`, or a `.env` file):

| Setting | Env var | Default | Notes |
|---|---|---|---|
| `ai_provider` | `EXO_AI_PROVIDER` | `echo` | `echo` / `openai` / `anthropic` |
| `ai_model` | `EXO_AI_MODEL` | provider default | optional model override |
| `ai_temperature` | `EXO_AI_TEMPERATURE` | `0.7` | |
| `ai_max_tokens` | `EXO_AI_MAX_TOKENS` | `1024` | |
| `ai_request_timeout` | `EXO_AI_REQUEST_TIMEOUT` | `60` | seconds |
| `openai_api_key` | `OPENAI_API_KEY` or `EXO_OPENAI_API_KEY` | — | |
| `openai_base_url` | `EXO_OPENAI_BASE_URL` | `https://api.openai.com/v1` | |
| `anthropic_api_key` | `ANTHROPIC_API_KEY` or `EXO_ANTHROPIC_API_KEY` | — | |
| `anthropic_base_url` | `EXO_ANTHROPIC_BASE_URL` | `https://api.anthropic.com/v1` | |
| `anthropic_version` | `EXO_ANTHROPIC_VERSION` | `2023-06-01` | |

Selecting a provider whose required key is missing raises
`ProviderConfigurationError`; an unknown provider name raises
`ProviderNotFoundError`.

## Usage

```python
from app.config import get_settings
from app.services.ai import ChatMessage, ProviderFactory

provider = ProviderFactory.create(get_settings())
messages = [ChatMessage(role="user", content="Hello!")]

# Single-shot
result = await provider.generate(messages)
print(result.content)

# Streaming
async for chunk in provider.stream(messages):
    print(chunk.delta, end="")

await provider.aclose()
```

## Adding a new provider

The design is open for extension and closed for modification: adding a provider
requires no change to `factory.py` or to any existing provider.

1. Create `backend/app/services/ai/providers/<name>.py`.
2. Subclass `AIProvider` (or `HttpChatProvider` for HTTP APIs), set a unique
   `name`, and implement `from_settings`, `generate`, and `stream`.
3. Decorate the class with `@ProviderFactory.register`.
4. Import it in `providers/__init__.py` so its registration runs at import time.

```python
from app.services.ai.factory import ProviderFactory
from app.services.ai.providers._httpbase import HttpChatProvider

@ProviderFactory.register
class MyProvider(HttpChatProvider):
    name = "my-provider"
    ...
```

## Testing

HTTP providers accept an injected `httpx.AsyncClient`, so tests run against
`httpx.MockTransport` with no network access. `EchoProvider` needs neither a key
nor a network and is the default used in tests and CI. See
`tests/test_ai_providers.py`.
