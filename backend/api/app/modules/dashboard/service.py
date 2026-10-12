from collections.abc import Callable
from datetime import UTC, datetime

from app.core.errors import ApplicationError
from app.modules.dashboard.domain import (
    AdminCounts,
    AdminDashboardResponse,
    CreativeCounts,
    CreativeDashboardResponse,
    DashboardSummaryResponse,
    DataStatus,
    OperationsCounts,
    OperationsDashboardResponse,
    ProcurementCounts,
    ProcurementDashboardResponse,
)
from app.modules.identity.domain import ModuleCode, Permission, Principal, to_viewer
from app.modules.registry import MODULES, ModuleStatus
from app.modules.workspace.domain import WorkspaceArea
from app.modules.workspace.repository import WorkspaceRepository

DEMO_DISCLAIMER = "Demo data only; it is not an authoritative operating fact."


class DashboardService:
    def __init__(
        self,
        repository: WorkspaceRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    async def get_summary(self, principal: Principal) -> DashboardSummaryResponse:
        requirements = (
            (ModuleCode.ADMIN, Permission.ADMIN_DASHBOARD_READ),
            (ModuleCode.OPERATIONS, Permission.OPERATIONS_DASHBOARD_READ),
            (ModuleCode.PROCUREMENT, Permission.PROCUREMENT_DASHBOARD_READ),
            (ModuleCode.CREATIVE, Permission.CREATIVE_DASHBOARD_READ),
        )
        for module, permission in requirements:
            if module in principal.modules and permission in principal.permissions:
                return await self.get_module_summary(principal, module)
        raise ApplicationError("WORKSPACE_NOT_AVAILABLE", "No authorized workspace", 403)

    async def get_module_summary(
        self, principal: Principal, module: ModuleCode
    ) -> DashboardSummaryResponse:
        required_permission = {
            ModuleCode.ADMIN: Permission.ADMIN_DASHBOARD_READ,
            ModuleCode.OPERATIONS: Permission.OPERATIONS_DASHBOARD_READ,
            ModuleCode.PROCUREMENT: Permission.PROCUREMENT_DASHBOARD_READ,
            ModuleCode.CREATIVE: Permission.CREATIVE_DASHBOARD_READ,
        }[module]
        if module not in principal.modules or required_permission not in principal.permissions:
            raise ApplicationError("WORKSPACE_NOT_AVAILABLE", "No authorized workspace", 403)

        common = {
            "viewer": to_viewer(principal),
            "generated_at": self._clock(),
            "data_status": DataStatus.DEMO,
            "disclaimer": DEMO_DISCLAIMER,
            "alerts": [],
        }
        if module is ModuleCode.ADMIN:
            return AdminDashboardResponse(
                workspace="admin",
                counts=AdminCounts(open_errors=0, pending_ai_feedback=0, audit_events=0),
                readable_modules=[
                    module.name for module in MODULES if module.status is ModuleStatus.ACTIVE
                ],
                **common,
            )
        if module is ModuleCode.OPERATIONS:
            records = await self._repository.list_scoped(principal, WorkspaceArea.OPERATIONS)
            projects = [record.response for record in records]
            return OperationsDashboardResponse(
                workspace="operations",
                counts=OperationsCounts(
                    pending_tasks=sum(item.status == "pending" for item in projects),
                    active_projects=len(projects),
                    exceptions=sum(item.status == "exception" for item in projects),
                ),
                work_items=[],
                projects=projects,
                **common,
            )
        if module is ModuleCode.PROCUREMENT:
            records = await self._repository.list_scoped(principal, WorkspaceArea.PROCUREMENT)
            requests = [record.response for record in records]
            return ProcurementDashboardResponse(
                workspace="procurement",
                counts=ProcurementCounts(
                    pending_requests=sum(item.status == "pending" for item in requests),
                    open_quotes=sum(item.record_type == "quote" for item in requests),
                    fulfillment_exceptions=sum(item.status == "exception" for item in requests),
                ),
                purchase_requests=requests,
                **common,
            )
        if module is ModuleCode.CREATIVE:
            records = await self._repository.list_scoped(principal, WorkspaceArea.CREATIVE)
            tasks = [record.response for record in records]
            return CreativeDashboardResponse(
                workspace="creative",
                counts=CreativeCounts(
                    pending_content_tasks=sum(item.status == "pending" for item in tasks),
                    assets_in_review=sum(item.status == "in_review" for item in tasks),
                    generation_failures=sum(item.status == "failed" for item in tasks),
                ),
                content_tasks=tasks,
                **common,
            )
        raise ApplicationError("WORKSPACE_NOT_AVAILABLE", "No authorized workspace", 403)
