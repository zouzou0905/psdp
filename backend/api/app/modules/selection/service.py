import json
from uuid import UUID

from app.core.errors import ApplicationError
from app.db.models import SelectionCompetitorVersion
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import Principal
from app.modules.selection.domain import (
    AiTaskListResponse,
    AiTaskResponse,
    CompetitorListResponse,
    CompetitorResponse,
    CompetitorUpsertRequest,
    FinalSelectionResponse,
    FinalSelectionUpsertRequest,
    ListingDraftResponse,
    ProfitReviewResponse,
    QuotationResponse,
    QuotationUpsertRequest,
    SelectionListResponse,
    SelectionRecordResponse,
)
from app.modules.selection.repository import (
    SelectionRevisionConflictError,
    SqlAlchemySelectionRepository,
)


class SelectionService:
    def __init__(
        self, repository: SqlAlchemySelectionRepository, audit_service: AuditService
    ) -> None:
        self._repository = repository
        self._audit_service = audit_service

    async def list_records(self, principal: Principal) -> SelectionListResponse:
        records = await self._repository.list_records(principal)
        return SelectionListResponse(
            items=[SelectionRecordResponse.model_validate(record) for record in records],
            total=len(records),
        )

    async def get_record(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionRecordResponse:
        record = await self._repository.get_record(principal, selection_id)
        if record is None:
            raise ApplicationError("SELECTION_NOT_FOUND", "Selection record not found", 404)
        return SelectionRecordResponse.model_validate(record)

    async def get_quotation(
        self, principal: Principal, selection_id: UUID
    ) -> QuotationResponse:
        quotation = await self._repository.get_quotation(principal, selection_id)
        if quotation is None:
            raise ApplicationError("QUOTATION_NOT_FOUND", "Quotation not found", 404)
        return QuotationResponse.model_validate(quotation)

    async def save_quotation(
        self,
        principal: Principal,
        selection_id: UUID,
        payload: QuotationUpsertRequest,
        trace_id: str | None,
    ) -> QuotationResponse:
        try:
            result = await self._repository.save_quotation(principal, selection_id, payload)
        except SelectionRevisionConflictError as exc:
            raise self._conflict() from exc
        if result is None:
            raise ApplicationError("SELECTION_NOT_FOUND", "Selection record not found", 404)
        record, quotation = result
        await self._audit(
            principal,
            "selection.quotation.save",
            selection_id,
            trace_id,
            {"version": str(quotation.version), "revision": str(record.revision)},
        )
        return QuotationResponse.model_validate(quotation)

    async def get_profit_review(
        self, principal: Principal, selection_id: UUID
    ) -> ProfitReviewResponse:
        review = await self._repository.get_profit_review(principal, selection_id)
        if review is None:
            raise ApplicationError(
                "PROFIT_REVIEW_NOT_AVAILABLE", "Profit review is not available", 404
            )
        return ProfitReviewResponse.model_validate(review)

    async def get_final_selection(
        self, principal: Principal, selection_id: UUID
    ) -> FinalSelectionResponse:
        final = await self._repository.get_final_selection(principal, selection_id)
        if final is None:
            raise ApplicationError(
                "FINAL_SELECTION_NOT_AVAILABLE", "Final selection is not available", 404
            )
        return FinalSelectionResponse.model_validate(final)

    async def save_final_selection(
        self,
        principal: Principal,
        selection_id: UUID,
        payload: FinalSelectionUpsertRequest,
        trace_id: str | None,
    ) -> FinalSelectionResponse:
        await self.get_record(principal, selection_id)
        try:
            result = await self._repository.save_final_selection(
                principal,
                selection_id,
                payload.decision,
                payload.reason,
                payload.expected_revision,
            )
        except SelectionRevisionConflictError as exc:
            raise self._conflict() from exc
        if result is None:
            raise ApplicationError(
                "PROFIT_REVIEW_REQUIRED",
                "A current profit review is required before final selection",
                409,
            )
        record, final = result
        await self._audit(
            principal,
            "selection.final.save",
            selection_id,
            trace_id,
            {
                "decision": final.decision,
                "version": str(final.version),
                "revision": str(record.revision),
            },
        )
        return FinalSelectionResponse.model_validate(final)

    async def save_competitors(
        self,
        principal: Principal,
        selection_id: UUID,
        payload: CompetitorUpsertRequest,
        trace_id: str | None,
    ) -> CompetitorListResponse:
        await self.get_record(principal, selection_id)
        try:
            result = await self._repository.save_competitors(
                principal,
                selection_id,
                payload.competitors,
                payload.expected_revision,
            )
        except SelectionRevisionConflictError as exc:
            raise self._conflict() from exc
        if result is None:
            raise ApplicationError(
                "FINAL_SELECTION_REQUIRED",
                "A selected final-selection version is required",
                409,
            )
        record, final, competitors = result
        await self._audit(
            principal,
            "selection.competitors.save",
            selection_id,
            trace_id,
            {
                "final_version": str(final.version),
                "competitor_count": str(len(competitors)),
                "revision": str(record.revision),
            },
        )
        return self._competitor_response(record.revision, final.version, competitors)

    async def get_competitors(
        self, principal: Principal, selection_id: UUID
    ) -> CompetitorListResponse:
        result = await self._repository.list_competitors(principal, selection_id)
        if result is None:
            raise ApplicationError("COMPETITORS_NOT_AVAILABLE", "Competitors not available", 404)
        record, final, competitors = result
        return self._competitor_response(record.revision, final.version, competitors)

    async def list_ai_tasks(
        self, principal: Principal, selection_id: UUID
    ) -> AiTaskListResponse:
        tasks = await self._repository.list_ai_tasks(principal, selection_id)
        if tasks is None:
            raise ApplicationError("SELECTION_NOT_FOUND", "Selection record not found", 404)
        return AiTaskListResponse(
            items=[AiTaskResponse.model_validate(task) for task in tasks], total=len(tasks)
        )

    async def get_listing_draft(
        self, principal: Principal, selection_id: UUID
    ) -> ListingDraftResponse:
        draft = await self._repository.get_listing_draft(principal, selection_id)
        if draft is None:
            raise ApplicationError(
                "LISTING_DRAFT_NOT_AVAILABLE",
                "No listing draft has been produced by an AI task",
                404,
            )
        return ListingDraftResponse.model_validate(draft)

    @staticmethod
    def _conflict() -> ApplicationError:
        return ApplicationError(
            "SELECTION_REVISION_CONFLICT",
            "Selection changed; reload before updating",
            409,
        )

    @staticmethod
    def _competitor_response(
        revision: int,
        final_version: int,
        competitors: list[SelectionCompetitorVersion],
    ) -> CompetitorListResponse:
        items = [CompetitorResponse.model_validate(item) for item in competitors]
        selection_id = competitors[0].selection_id if competitors else None
        if selection_id is None:
            raise ApplicationError("COMPETITORS_NOT_AVAILABLE", "Competitors not available", 404)
        return CompetitorListResponse(
            selection_id=selection_id,
            final_version=final_version,
            competitors=items,
            revision=revision,
        )

    async def _audit(
        self,
        principal: Principal,
        action: str,
        selection_id: UUID,
        trace_id: str | None,
        metadata: dict[str, str],
    ) -> None:
        await self._audit_service.record(
            action=action,
            resource_type="selection_record",
            resource_id=str(selection_id),
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={"change": json.dumps(metadata, sort_keys=True)},
        )
