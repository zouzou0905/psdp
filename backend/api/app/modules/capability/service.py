from app.integrations.deepseek import DeepSeekConnectionStatus, DeepSeekProvider
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import Principal


class CapabilityStatusService:
    def __init__(self, provider: DeepSeekProvider, audit_service: AuditService) -> None:
        self._provider = provider
        self._audit_service = audit_service

    async def deepseek_status(
        self, principal: Principal, trace_id: str | None
    ) -> DeepSeekConnectionStatus:
        status = await self._provider.check_connection()
        await self._audit_service.record(
            action="admin.capability.deepseek.status.read",
            resource_type="capability",
            resource_id=DeepSeekProvider.capability_id,
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={
                "configured": str(status.configured).lower(),
                "reachable": str(status.reachable).lower(),
                "status": status.status,
                "error_code": status.error_code or "none",
            },
        )
        return status
