from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.identity.domain import RoleName


class AuditResult(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILURE = "failure"


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    audit_id: UUID
    actor_id: UUID | None
    actor_roles: tuple[RoleName, ...]
    action: str
    resource_type: str
    resource_id: str | None
    result: AuditResult
    trace_id: str | None
    occurred_at: datetime
    metadata_summary: dict[str, str]


class AuditLogResponse(AuditEvent):
    pass
