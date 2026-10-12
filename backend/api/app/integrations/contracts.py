from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.modules.identity.domain import DataScope, ModuleCode


class ExternalCallContext(BaseModel):
    """Mandatory authorization and trace context for every future external call."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: UUID
    module_code: ModuleCode
    store_id: str = Field(min_length=1)
    permission_scope: DataScope
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)


class CapabilityGateway(Protocol):
    async def invoke(
        self, capability_id: str, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]: ...


class CapabilityProvider(Protocol):
    async def invoke(
        self, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]: ...


class MCPClientAdapter(Protocol):
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]: ...


class MarketplaceConnector(Protocol):
    async def execute(
        self, operation: str, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]: ...


class ERPConnector(Protocol):
    async def execute(
        self, operation: str, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]: ...


class StoreCredentialProvider(Protocol):
    async def get_credential(self, store_id: str, context: ExternalCallContext) -> SecretStr: ...
