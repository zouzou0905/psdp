import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from app.integrations.contracts import ExternalCallContext

Sleep = Callable[[float], Awaitable[None]]


class DeepSeekProviderError(Exception):
    code = "DEEPSEEK_PROVIDER_ERROR"


class DeepSeekNotConfiguredError(DeepSeekProviderError):
    code = "DEEPSEEK_NOT_CONFIGURED"


class DeepSeekTimeoutError(DeepSeekProviderError):
    code = "DEEPSEEK_TIMEOUT"


class DeepSeekRateLimitError(DeepSeekProviderError):
    code = "DEEPSEEK_RATE_LIMITED"


class DeepSeekAuthenticationError(DeepSeekProviderError):
    code = "DEEPSEEK_AUTHENTICATION_FAILED"


class DeepSeekUnavailableError(DeepSeekProviderError):
    code = "DEEPSEEK_UNAVAILABLE"


class DeepSeekResponseStructureError(DeepSeekProviderError):
    code = "DEEPSEEK_INVALID_RESPONSE"


class DeepSeekRequestRejectedError(DeepSeekProviderError):
    code = "DEEPSEEK_REQUEST_REJECTED"


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1)


class ChatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    response_format: dict[str, str] | None = None


class DeepSeekConnectionStatus(BaseModel):
    configured: bool
    reachable: bool
    status: str
    endpoint_host: str | None
    model: str | None
    latency_ms: int | None
    error_code: str | None


class DeepSeekProvider:
    capability_id = "deepseek.chat"

    def __init__(
        self,
        *,
        api_key: SecretStr | None,
        base_url: SecretStr,
        model: SecretStr,
        connect_timeout_seconds: float,
        request_timeout_seconds: float,
        max_retries: int,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.get_secret_value().rstrip("/")
        self._model = model.get_secret_value()
        self._timeout = httpx.Timeout(
            request_timeout_seconds, connect=connect_timeout_seconds
        )
        self._max_retries = max_retries
        self._transport = transport
        self._sleep = sleep

    async def invoke(
        self, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]:
        del context  # The gateway validates and propagates it; prompts never enter logs here.
        self._ensure_configured()
        try:
            request = ChatPayload.model_validate(payload)
        except ValidationError as exc:
            raise DeepSeekRequestRejectedError("Invalid DeepSeek request structure") from exc
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [message.model_dump() for message in request.messages],
        }
        for field in ("temperature", "max_tokens", "response_format"):
            value = getattr(request, field)
            if value is not None:
                body[field] = value
        response = await self._request("POST", "/chat/completions", json=body)
        try:
            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise TypeError
            usage = data.get("usage")
            if usage is not None and not isinstance(usage, dict):
                raise TypeError
            return {
                "provider": "deepseek",
                "model": str(data.get("model") or self._model),
                "content": content,
                "finish_reason": choice.get("finish_reason"),
                "usage": usage or {},
            }
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise DeepSeekResponseStructureError(
                "DeepSeek returned an invalid response structure"
            ) from exc

    async def check_connection(self) -> DeepSeekConnectionStatus:
        host = urlparse(self._base_url).hostname
        if self._api_key is None or not self._api_key.get_secret_value():
            return DeepSeekConnectionStatus(
                configured=False,
                reachable=False,
                status="not_configured",
                endpoint_host=host,
                model=self._model or None,
                latency_ms=None,
                error_code=DeepSeekNotConfiguredError.code,
            )
        started = perf_counter()
        try:
            response = await self._request("GET", "/models")
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise DeepSeekResponseStructureError(
                    "DeepSeek returned an invalid response structure"
                )
        except DeepSeekProviderError as exc:
            return DeepSeekConnectionStatus(
                configured=True,
                reachable=False,
                status="unavailable",
                endpoint_host=host,
                model=self._model or None,
                latency_ms=round((perf_counter() - started) * 1000),
                error_code=exc.code,
            )
        except (TypeError, ValueError):
            return DeepSeekConnectionStatus(
                configured=True,
                reachable=False,
                status="unavailable",
                endpoint_host=host,
                model=self._model or None,
                latency_ms=round((perf_counter() - started) * 1000),
                error_code=DeepSeekResponseStructureError.code,
            )
        return DeepSeekConnectionStatus(
            configured=True,
            reachable=True,
            status="available",
            endpoint_host=host,
            model=self._model,
            latency_ms=round((perf_counter() - started) * 1000),
            error_code=None,
        )

    def _ensure_configured(self) -> None:
        if self._api_key is None or not self._api_key.get_secret_value():
            raise DeepSeekNotConfiguredError("DeepSeek is not configured")

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> httpx.Response:
        self._ensure_configured()
        assert self._api_key is not None
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    transport=self._transport,
                    follow_redirects=False,
                ) as client:
                    response = await client.request(
                        method, f"{self._base_url}{path}", headers=headers, json=json
                    )
            except httpx.TimeoutException as exc:
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise DeepSeekTimeoutError("DeepSeek request timed out") from exc
            except httpx.TransportError as exc:
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise DeepSeekUnavailableError("DeepSeek is unavailable") from exc

            if response.status_code in {401, 403}:
                raise DeepSeekAuthenticationError("DeepSeek authentication failed")
            if response.status_code == 429:
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise DeepSeekRateLimitError("DeepSeek rate limit reached")
            if response.status_code >= 500:
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise DeepSeekUnavailableError("DeepSeek is unavailable")
            if response.status_code >= 400:
                raise DeepSeekRequestRejectedError("DeepSeek rejected the request")
            return response
        raise DeepSeekUnavailableError("DeepSeek is unavailable")

    async def _backoff(self, attempt: int) -> None:
        await self._sleep(min(0.25 * (2**attempt), 1.0))
