from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from app.integrations.deepseek import DeepSeekConnectionStatus
from app.modules.authorization.dependencies import require_access
from app.modules.capability.service import CapabilityStatusService
from app.modules.identity.domain import ModuleCode, Permission, Principal

router = APIRouter(prefix="/admin/capabilities", tags=["admin-capabilities"])


def get_capability_status_service(request: Request) -> CapabilityStatusService:
    return cast(CapabilityStatusService, request.app.state.capability_status_service)


@router.get("/deepseek/status", response_model=DeepSeekConnectionStatus)
async def deepseek_status(
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.CAPABILITY_READ)),
    ],
    service: Annotated[CapabilityStatusService, Depends(get_capability_status_service)],
) -> DeepSeekConnectionStatus:
    return await service.deepseek_status(
        principal, getattr(request.state, "trace_id", None)
    )
