from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, Request

from app.modules.admin.domain import (
    AiFeedbackListResponse,
    AuditLogListResponse,
    ErrorListResponse,
)
from app.modules.admin.service import AdminQueryService
from app.modules.authorization.dependencies import require_access
from app.modules.identity.domain import ModuleCode, Permission, Principal

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_query_service(request: Request) -> AdminQueryService:
    return cast(AdminQueryService, request.app.state.admin_query_service)


@router.get("/errors", response_model=ErrorListResponse)
async def list_errors(
    request: Request,
    principal: Annotated[
        Principal, Depends(require_access(ModuleCode.ADMIN, Permission.ERROR_READ))
    ],
    service: Annotated[AdminQueryService, Depends(get_admin_query_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> ErrorListResponse:
    return await service.list_errors(principal, getattr(request.state, "trace_id", None), limit)


@router.get("/ai-feedback", response_model=AiFeedbackListResponse)
async def list_ai_feedback(
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.AI_FEEDBACK_READ_ALL)),
    ],
    service: Annotated[AdminQueryService, Depends(get_admin_query_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> AiFeedbackListResponse:
    return await service.list_ai_feedback(
        principal, getattr(request.state, "trace_id", None), limit
    )


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    request: Request,
    principal: Annotated[
        Principal, Depends(require_access(ModuleCode.ADMIN, Permission.AUDIT_LOG_READ))
    ],
    service: Annotated[AdminQueryService, Depends(get_admin_query_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> AuditLogListResponse:
    return await service.list_audit_logs(principal, getattr(request.state, "trace_id", None), limit)
