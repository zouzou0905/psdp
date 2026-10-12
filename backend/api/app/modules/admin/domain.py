from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.audit.domain import AuditLogResponse


class ErrorCategory(StrEnum):
    SYSTEM = "system"
    API = "api"
    WORKER = "worker"
    INTEGRATION = "integration"
    AI_CAPABILITY = "ai_capability"
    EXTERNAL_STATUS_UNKNOWN = "external_status_unknown"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecordStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ErrorRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    error_id: UUID
    category: ErrorCategory
    severity: Severity
    status: RecordStatus
    module: str
    task_id: str | None
    run_id: str | None
    action_id: str | None
    summary: str
    occurred_at: datetime
    resolved_at: datetime | None
    trace_id: str | None


class FeedbackStatus(StrEnum):
    NEW = "new"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AiFeedback(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    feedback_id: UUID
    task_id: str
    run_id: str
    capability_id: str
    capability_release_id: str
    submitted_by: UUID
    feedback_type: str
    summary: str
    status: FeedbackStatus
    created_at: datetime


class ErrorListResponse(BaseModel):
    items: list[ErrorRecord]
    total: int = Field(ge=0)


class AiFeedbackListResponse(BaseModel):
    items: list[AiFeedback]
    total: int = Field(ge=0)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int = Field(ge=0)
