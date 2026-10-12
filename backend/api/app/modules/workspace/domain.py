from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.identity.domain import DataScope


class WorkspaceArea(StrEnum):
    OPERATIONS = "operations"
    PROCUREMENT = "procurement"
    CREATIVE = "creative"


class WorkspaceRecordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID
    store_id: str | None
    record_type: str
    title: str
    status: str
    updated_at: datetime
    summary: dict[str, object]


class ScopedWorkspaceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    response: WorkspaceRecordResponse
    area: WorkspaceArea
    assignee_id: UUID | None
    owner_id: UUID | None
    scope: DataScope


class WorkspaceRecordListResponse(BaseModel):
    items: list[WorkspaceRecordResponse]
    total: int
