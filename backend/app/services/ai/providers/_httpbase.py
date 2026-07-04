"""Shared base for providers that call a remote HTTP chat API.

Encapsulates the ``httpx.AsyncClient`` lifecycle and the two transport
patterns every HTTP provider needs: a JSON POST for single-shot generation
and a Server-Sent-Events (SSE) reader for streaming. A client may be injected
(dependency injection) which makes providers trivially testable against
``httpx.MockTransport`` without any network access.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

import httpx

from app.services.ai.base import AIProvider, AIProviderError


class HttpChatProvider(AIProvider):
    """Base class for HTTP-backed chat providers (OpenAI, Anthropic, ...)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float,
        default_temperature: float,
        default_max_tokens: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        # Track whether we own the client so an injected one is never closed.
        self._client = client
        self._owns_client = client is None

    @property
    def model(self) -> str | None:
        return self._model

    # -- resource management ------------------------------------------------

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    # -- to be provided by concrete providers ------------------------------

    def _headers(self) -> dict[str, str]:
        """Return provider-specific request headers (auth, versioning)."""
        raise NotImplementedError

    # -- transport helpers -------------------------------------------------

    async def _post_json(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """POST ``payload`` as JSON and return the decoded response body."""
        client = self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}{path}", json=dict(payload), headers=self._headers()
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network failure path
            raise AIProviderError(f"{self.name} request failed: {exc}") from exc
        self._raise_for_status(response)
        body: dict[str, Any] = response.json()
        return body

    async def _iter_sse(self, path: str, payload: Mapping[str, Any]) -> AsyncIterator[str]:
        """Stream an SSE response, yielding each ``data:`` payload string.

        The terminal ``[DONE]`` sentinel (used by OpenAI) ends iteration; other
        providers simply close the connection, which also ends iteration.
        """
        client = self._get_client()
        try:
            async with client.stream(
                "POST",
                f"{self._base_url}{path}",
                json=dict(payload),
                headers=self._headers(),
            ) as response:
                if response.status_code >= 400:
                    detail = (await response.aread()).decode("utf-8", "replace")
                    raise AIProviderError(
                        f"{self.name} streaming request failed "
                        f"(HTTP {response.status_code}): {detail}"
                    )
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    yield data
        except httpx.HTTPError as exc:  # pragma: no cover - network failure path
            raise AIProviderError(f"{self.name} streaming request failed: {exc}") from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise AIProviderError(
                f"{self.name} request failed (HTTP {response.status_code}): {response.text}"
            )

    # -- shared resolution helpers -----------------------------------------

    def _resolve_model(self, model: str | None) -> str:
        return model or self._model

    def _resolve_temperature(self, temperature: float | None) -> float:
        return temperature if temperature is not None else self._default_temperature

    def _resolve_max_tokens(self, max_tokens: int | None) -> int:
        return max_tokens if max_tokens is not None else self._default_max_tokens
