from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from app.modules.authorization.dependencies import require_any_access
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.selection_skill.domain import SelectionSkillDetail, SelectionSkillListResponse
from app.modules.selection_skill.service import SelectionSkillService

router = APIRouter(prefix="/selection-skills", tags=["selection-skills"])

READ_SKILL_REGISTRY = require_any_access(
    (ModuleCode.PROCUREMENT, Permission.SELECTION_READ),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)


def get_selection_skill_service(request: Request) -> SelectionSkillService:
    return cast(SelectionSkillService, request.app.state.selection_skill_service)


@router.get("", response_model=SelectionSkillListResponse)
async def list_selection_skills(
    request: Request,
    principal: Annotated[Principal, Depends(READ_SKILL_REGISTRY)],
    service: Annotated[SelectionSkillService, Depends(get_selection_skill_service)],
) -> SelectionSkillListResponse:
    return await service.list_skills(principal, getattr(request.state, "trace_id", None))


@router.get("/{skill_key}", response_model=SelectionSkillDetail)
async def get_selection_skill(
    skill_key: str,
    request: Request,
    principal: Annotated[Principal, Depends(READ_SKILL_REGISTRY)],
    service: Annotated[SelectionSkillService, Depends(get_selection_skill_service)],
) -> SelectionSkillDetail:
    return await service.get_skill(
        principal, skill_key, getattr(request.state, "trace_id", None)
    )
