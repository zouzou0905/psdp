from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.modules.authorization.dependencies import require_access
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.workspace.domain import (
    WorkspaceArea,
    WorkspaceRecordListResponse,
    WorkspaceRecordResponse,
)
from app.modules.workspace.service import WorkspaceService

router = APIRouter(tags=["role-workspaces"])


def get_workspace_service(request: Request) -> WorkspaceService:
    return cast(WorkspaceService, request.app.state.workspace_service)


@router.get("/operations/projects", response_model=WorkspaceRecordListResponse)
async def list_operations_projects(
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.OPERATIONS, Permission.PROJECT_READ_ASSIGNED)),
    ],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceRecordListResponse:
    return await service.list_records(principal, WorkspaceArea.OPERATIONS)


@router.get("/operations/projects/{record_id}", response_model=WorkspaceRecordResponse)
async def get_operations_project(
    record_id: UUID,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.OPERATIONS, Permission.PROJECT_READ_ASSIGNED)),
    ],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceRecordResponse:
    return await service.get_record(
        principal,
        WorkspaceArea.OPERATIONS,
        record_id,
        getattr(request.state, "trace_id", None),
    )


@router.get("/procurement/purchase-requests", response_model=WorkspaceRecordListResponse)
async def list_purchase_requests(
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.PROCUREMENT, Permission.PURCHASE_REQUEST_READ)),
    ],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceRecordListResponse:
    return await service.list_records(principal, WorkspaceArea.PROCUREMENT)


@router.get("/creative/content-tasks", response_model=WorkspaceRecordListResponse)
async def list_content_tasks(
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.CREATIVE, Permission.CONTENT_TASK_READ_ASSIGNED)),
    ],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceRecordListResponse:
    return await service.list_records(principal, WorkspaceArea.CREATIVE)
