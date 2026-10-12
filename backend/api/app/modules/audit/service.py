from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.audit.domain import AuditEvent, AuditResult
from app.modules.audit.repository import AuditRepository
from app.modules.identity.domain import Principal, RoleName


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        action: str,
        resource_type: str,
        result: AuditResult,
        trace_id: str | None,
        principal: Principal | None = None,
        actor_id: UUID | None = None,
        actor_roles: tuple[RoleName, ...] = (),
        resource_id: str | None = None,
        metadata_summary: dict[str, str] | None = None,
    ) -> None:
        await self._repository.append(
            AuditEvent(
                audit_id=uuid4(),
                actor_id=principal.user_id if principal else actor_id,
                actor_roles=tuple(sorted(principal.roles)) if principal else actor_roles,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                trace_id=trace_id,
                occurred_at=datetime.now(UTC),
                metadata_summary=metadata_summary or {},
            )
        )

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]:
        return await self._repository.list_recent(limit)
