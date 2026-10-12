from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.identity.domain import ViewerResponse
from app.modules.workspace.domain import WorkspaceRecordResponse


class DataStatus(StrEnum):
    DEMO = "demo"


class DashboardBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    viewer: ViewerResponse
    generated_at: datetime
    data_status: DataStatus
    disclaimer: str


class OperationsCounts(BaseModel):
    pending_tasks: int = Field(ge=0)
    active_projects: int = Field(ge=0)
    exceptions: int = Field(ge=0)


class OperationsDashboardResponse(DashboardBase):
    workspace: Literal["operations"]
    counts: OperationsCounts
    work_items: list[WorkspaceRecordResponse]
    projects: list[WorkspaceRecordResponse]
    alerts: list[str]


class ProcurementCounts(BaseModel):
    pending_requests: int = Field(ge=0)
    open_quotes: int = Field(ge=0)
    fulfillment_exceptions: int = Field(ge=0)


class ProcurementDashboardResponse(DashboardBase):
    workspace: Literal["procurement"]
    counts: ProcurementCounts
    purchase_requests: list[WorkspaceRecordResponse]
    alerts: list[str]


class CreativeCounts(BaseModel):
    pending_content_tasks: int = Field(ge=0)
    assets_in_review: int = Field(ge=0)
    generation_failures: int = Field(ge=0)


class CreativeDashboardResponse(DashboardBase):
    workspace: Literal["creative"]
    counts: CreativeCounts
    content_tasks: list[WorkspaceRecordResponse]
    alerts: list[str]


class AdminCounts(BaseModel):
    open_errors: int = Field(ge=0)
    pending_ai_feedback: int = Field(ge=0)
    audit_events: int = Field(ge=0)


class AdminDashboardResponse(DashboardBase):
    workspace: Literal["admin"]
    counts: AdminCounts
    readable_modules: list[str]
    alerts: list[str]


DashboardSummaryResponse = Annotated[
    OperationsDashboardResponse
    | ProcurementDashboardResponse
    | CreativeDashboardResponse
    | AdminDashboardResponse,
    Field(discriminator="workspace"),
]
