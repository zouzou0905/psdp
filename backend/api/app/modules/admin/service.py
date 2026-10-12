from datetime import UTC, datetime
from uuid import uuid4

from app.modules.admin.domain import (
    AiFeedback,
    AiFeedbackListResponse,
    AuditLogListResponse,
    ErrorCategory,
    ErrorListResponse,
    ErrorRecord,
    RecordStatus,
    Severity,
)
from app.modules.admin.redaction import RedactionService
from app.modules.admin.repository import AdminRepository
from app.modules.audit.domain import AuditEvent, AuditLogResponse, AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import Principal


class AdminQueryService:
    def __init__(
        self,
        repository: AdminRepository,
        audit_service: AuditService,
        redaction_service: RedactionService,
    ) -> None:
        self._repository = repository
        self._audit_service = audit_service
        self._redaction = redaction_service

    async def record_unexpected(self, exc: Exception, trace_id: str | None, path: str) -> None:
        await self._repository.append_error(
            ErrorRecord(
                error_id=uuid4(),
                category=ErrorCategory.API,
                severity=Severity.ERROR,
                status=RecordStatus.OPEN,
                module="api",
                task_id=None,
                run_id=None,
                action_id=None,
                summary=self._redaction.redact_text(f"{type(exc).__name__}: {exc}"),
                occurred_at=datetime.now(UTC),
                resolved_at=None,
                trace_id=trace_id,
            )
        )

    async def list_errors(
        self, principal: Principal, trace_id: str | None, limit: int
    ) -> ErrorListResponse:
        records = await self._repository.list_errors(limit)
        safe_records = [
            ErrorRecord(
                **record.model_dump(exclude={"summary"}),
                summary=self._redaction.redact_text(record.summary),
            )
            for record in records
        ]
        await self._record_sensitive_read(principal, trace_id, "error", len(safe_records))
        return ErrorListResponse(items=safe_records, total=len(safe_records))

    async def list_ai_feedback(
        self, principal: Principal, trace_id: str | None, limit: int
    ) -> AiFeedbackListResponse:
        records = await self._repository.list_ai_feedback(limit)
        safe_records = [
            AiFeedback(
                **record.model_dump(exclude={"summary"}),
                summary=self._redaction.redact_text(record.summary),
            )
            for record in records
        ]
        await self._record_sensitive_read(principal, trace_id, "ai_feedback", len(safe_records))
        return AiFeedbackListResponse(items=safe_records, total=len(safe_records))

    async def list_audit_logs(
        self, principal: Principal, trace_id: str | None, limit: int
    ) -> AuditLogListResponse:
        records = await self._audit_service.list_recent(limit)
        safe_records = [self._redact_audit(record) for record in records]
        await self._record_sensitive_read(principal, trace_id, "audit_log", len(safe_records))
        return AuditLogListResponse(items=safe_records, total=len(safe_records))

    def _redact_audit(self, record: AuditEvent) -> AuditLogResponse:
        safe_metadata = self._redaction.redact(record.metadata_summary)
        return AuditLogResponse(
            **record.model_dump(exclude={"metadata_summary"}),
            metadata_summary=safe_metadata,
        )

    async def _record_sensitive_read(
        self,
        principal: Principal,
        trace_id: str | None,
        resource_type: str,
        count: int,
    ) -> None:
        await self._audit_service.record(
            action=f"admin.{resource_type}.read",
            resource_type=resource_type,
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={"returned_count": str(count)},
        )
