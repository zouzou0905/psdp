from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import Principal
from app.modules.selection_skill.domain import SelectionSkillDetail, SelectionSkillListResponse
from app.modules.selection_skill.registry import SkillRegistry


class SelectionSkillService:
    def __init__(self, registry: SkillRegistry, audit_service: AuditService) -> None:
        self._registry = registry
        self._audit_service = audit_service

    async def list_skills(
        self, principal: Principal, trace_id: str | None
    ) -> SelectionSkillListResponse:
        result = self._registry.list_skills()
        await self._audit_service.record(
            action="selection_skill.registry.list",
            resource_type="selection_skill_registry",
            resource_id=None,
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={"returned_count": str(result.total)},
        )
        return result

    async def get_skill(
        self, principal: Principal, skill_key: str, trace_id: str | None
    ) -> SelectionSkillDetail:
        result = self._registry.get_skill(skill_key)
        if result is None:
            raise ApplicationError("SELECTION_SKILL_NOT_FOUND", "Selection Skill not found", 404)
        await self._audit_service.record(
            action="selection_skill.registry.read",
            resource_type="selection_skill",
            resource_id=skill_key,
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={"bundle_version": result.bundle_version},
        )
        return result
