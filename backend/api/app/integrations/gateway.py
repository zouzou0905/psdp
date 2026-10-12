from typing import Any

from app.integrations.contracts import CapabilityProvider, ExternalCallContext


class CapabilityNotRegisteredError(Exception):
    pass


class RoutedCapabilityGateway:
    def __init__(self, providers: dict[str, CapabilityProvider] | None = None) -> None:
        self._providers = dict(providers or {})

    def register(self, capability_id: str, provider: CapabilityProvider) -> None:
        self._providers[capability_id] = provider

    async def invoke(
        self, capability_id: str, payload: dict[str, Any], context: ExternalCallContext
    ) -> dict[str, Any]:
        provider = self._providers.get(capability_id)
        if provider is None:
            raise CapabilityNotRegisteredError(capability_id)
        return await provider.invoke(payload, context)
