from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from app.modules.authorization.dependencies import get_current_user, require_access
from app.modules.dashboard.domain import (
    AdminDashboardResponse,
    CreativeDashboardResponse,
    DashboardSummaryResponse,
    OperationsDashboardResponse,
    ProcurementDashboardResponse,
)
from app.modules.dashboard.service import DashboardService
from app.modules.identity.domain import ModuleCode, Permission, Principal

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(request: Request) -> DashboardService:
    return cast(DashboardService, request.app.state.dashboard_service)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get the role workspace summary",
)
async def get_dashboard_summary(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    principal: Annotated[
        Principal,
        Depends(get_current_user),
    ],
) -> DashboardSummaryResponse:
    return await service.get_summary(principal)


module_router = APIRouter(tags=["module-dashboards"])


@module_router.get("/operations/dashboard", response_model=OperationsDashboardResponse)
async def get_operations_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.OPERATIONS, Permission.OPERATIONS_DASHBOARD_READ)),
    ],
) -> OperationsDashboardResponse:
    return cast(
        OperationsDashboardResponse,
        await service.get_module_summary(principal, ModuleCode.OPERATIONS),
    )


@module_router.get("/procurement/dashboard", response_model=ProcurementDashboardResponse)
async def get_procurement_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.PROCUREMENT, Permission.PROCUREMENT_DASHBOARD_READ)),
    ],
) -> ProcurementDashboardResponse:
    return cast(
        ProcurementDashboardResponse,
        await service.get_module_summary(principal, ModuleCode.PROCUREMENT),
    )


@module_router.get("/creative/dashboard", response_model=CreativeDashboardResponse)
async def get_creative_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.CREATIVE, Permission.CREATIVE_DASHBOARD_READ)),
    ],
) -> CreativeDashboardResponse:
    return cast(
        CreativeDashboardResponse,
        await service.get_module_summary(principal, ModuleCode.CREATIVE),
    )


@module_router.get("/admin/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.ADMIN_DASHBOARD_READ)),
    ],
) -> AdminDashboardResponse:
    return cast(
        AdminDashboardResponse,
        await service.get_module_summary(principal, ModuleCode.ADMIN),
    )
