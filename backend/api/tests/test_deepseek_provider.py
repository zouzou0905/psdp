import os
from typing import Any
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.integrations.contracts import ExternalCallContext
from app.integrations.deepseek import (
    DeepSeekAuthenticationError,
    DeepSeekProvider,
    DeepSeekRateLimitError,
    DeepSeekResponseStructureError,
    DeepSeekTimeoutError,
)
from app.integrations.gateway import RoutedCapabilityGateway
from app.modules.identity.domain import DataScope, ModuleCode


async def _no_sleep(_seconds: float) -> None:
    return None


def _context() -> ExternalCallContext:
    return ExternalCallContext(
        user_id=uuid4(),
        module_code=ModuleCode.PROCUREMENT,
        store_id="store_test",
        permission_scope=DataScope(store_ids=frozenset({"store_test"})),
        task_id="tsk_test",
        run_id="run_test",
        action_id="act_test",
    )


def _provider(
    handler: Any, *, max_retries: int = 2, api_key: str = "test-secret-key"
) -> DeepSeekProvider:
    return DeepSeekProvider(
        api_key=SecretStr(api_key),
        base_url=SecretStr("https://api.deepseek.test"),
        model=SecretStr("deepseek-chat"),
        connect_timeout_seconds=1,
        request_timeout_seconds=2,
        max_retries=max_retries,
        transport=httpx.MockTransport(handler),
        sleep=_no_sleep,
    )


async def test_gateway_routes_successful_deepseek_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-secret-key"
        return httpx.Response(
            200,
            json={
                "model": "deepseek-chat",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "OK"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 2, "completion_tokens": 1},
            },
        )

    provider = _provider(handler)
    gateway = RoutedCapabilityGateway({DeepSeekProvider.capability_id: provider})
    result = await gateway.invoke(
        "deepseek.chat",
        {"messages": [{"role": "user", "content": "health check"}]},
        _context(),
    )
    assert result["content"] == "OK"
    assert result["provider"] == "deepseek"
    assert "test-secret-key" not in str(result)


async def test_deepseek_timeout_is_retried_and_safely_classified() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("mock timeout", request=request)

    with pytest.raises(DeepSeekTimeoutError, match="timed out") as error:
        await _provider(handler).invoke(
            {"messages": [{"role": "user", "content": "sensitive prompt"}]}, _context()
        )
    assert attempts == 3
    assert "sensitive prompt" not in str(error.value)
    assert "test-secret-key" not in str(error.value)


async def test_deepseek_rate_limit_uses_finite_retries() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, json={"error": {"message": "do not expose"}})

    with pytest.raises(DeepSeekRateLimitError):
        await _provider(handler).invoke(
            {"messages": [{"role": "user", "content": "hello"}]}, _context()
        )
    assert attempts == 3


async def test_deepseek_authentication_failure_is_not_retried() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    with pytest.raises(DeepSeekAuthenticationError):
        await _provider(handler).invoke(
            {"messages": [{"role": "user", "content": "hello"}]}, _context()
        )
    assert attempts == 1


async def test_deepseek_invalid_response_structure_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    with pytest.raises(DeepSeekResponseStructureError):
        await _provider(handler).invoke(
            {"messages": [{"role": "user", "content": "hello"}]}, _context()
        )


async def test_deepseek_status_does_not_return_credentials(
    client: httpx.AsyncClient,
    app: Any,
    auth_headers: dict[Any, dict[str, str]],
) -> None:
    from app.modules.capability.service import CapabilityStatusService
    from app.modules.identity.domain import RoleName

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"object": "list", "data": []})

    provider = _provider(handler, api_key="status-secret-key")
    app.state.capability_status_service = CapabilityStatusService(
        provider, app.state.audit_service
    )
    denied = await client.get(
        "/api/v1/admin/capabilities/deepseek/status",
        headers=auth_headers[RoleName.OPERATIONS],
    )
    assert denied.status_code == 403
    response = await client.get(
        "/api/v1/admin/capabilities/deepseek/status",
        headers=auth_headers[RoleName.ADMIN],
    )
    assert response.status_code == 200
    assert response.json()["status"] == "available"
    serialized = response.text.lower()
    assert "status-secret-key" not in serialized
    assert "authorization" not in serialized
    assert "api_key" not in serialized


@pytest.mark.skipif(
    os.environ.get("RUN_DEEPSEEK_LIVE_TESTS") != "1",
    reason="Set RUN_DEEPSEEK_LIVE_TESTS=1 to call the configured DeepSeek API",
)
async def test_live_deepseek_chat_provider() -> None:
    settings = Settings()
    assert settings.deepseek_api_key is not None
    provider = DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        connect_timeout_seconds=settings.deepseek_connect_timeout_seconds,
        request_timeout_seconds=settings.deepseek_request_timeout_seconds,
        max_retries=settings.deepseek_max_retries,
    )
    result = await provider.invoke(
        {
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "max_tokens": 128,
        },
        _context(),
    )
    assert isinstance(result["content"], str)
    assert result["content"].strip()
