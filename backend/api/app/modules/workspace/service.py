from uuid import UUID

from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.authorization.dependencies import enforce_scope
from app.modules.identity.domain import Principal
from app.modules.workspace.domain import (
    WorkspaceArea,
    WorkspaceRecordListResponse,
    WorkspaceRecordResponse,
)
from app.modules.workspace.repository import WorkspaceRepository


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository, audit_service: AuditService) -> None:
        self._repository = repository
        self._audit_service = audit_service

    async def list_records(
        self, principal: Principal, area: WorkspaceArea
    ) -> WorkspaceRecordListResponse:
        records = await self._repository.list_scoped(principal, area)
        for record in records:
            assigned_user_id = (
                principal.user_id
                if principal.user_id in {record.assignee_id, record.owner_id}
                else record.assignee_id or record.owner_id
            )
            enforce_scope(
                principal,
                record.scope,
                assigned_user_id=assigned_user_id,
            )
        return WorkspaceRecordListResponse(
            items=[record.response for record in records], total=len(records)
        )

    async def get_record(
        self,
        principal: Principal,
        area: WorkspaceArea,
        record_id: UUID,
        trace_id: str | None,
    ) -> WorkspaceRecordResponse:
        record = await self._repository.get_scoped(principal, area, record_id)
        if record is None:
            await self._audit_service.record(
                action="authorization.scope_denied_or_not_found",
                resource_type=area.value,
                resource_id=str(record_id),
                result=AuditResult.DENIED,
                trace_id=trace_id,
                principal=principal,
            )
            raise ApplicationError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        assigned_user_id = (
            principal.user_id
            if principal.user_id in {record.assignee_id, record.owner_id}
            else record.assignee_id or record.owner_id
        )
        enforce_scope(
            principal,
            record.scope,
            assigned_user_id=assigned_user_id,
        )
        return record.response
