from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.modules.authorization.dependencies import require_any_access
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.selection.domain import (
    AiTaskListResponse,
    CompetitorListResponse,
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
from app.modules.selection.service import SelectionService

router = APIRouter(prefix="/selection-records", tags=["selection-flow"])

READ_SELECTION = require_any_access(
    (ModuleCode.OPERATIONS, Permission.SELECTION_READ),
    (ModuleCode.PROCUREMENT, Permission.SELECTION_READ),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
READ_QUOTATION = require_any_access(
    (ModuleCode.PROCUREMENT, Permission.QUOTE_READ),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
MANAGE_QUOTATION = require_any_access(
    (ModuleCode.PROCUREMENT, Permission.QUOTE_MANAGE),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
READ_PROFIT = require_any_access(
    (ModuleCode.OPERATIONS, Permission.PROFIT_REVIEW_READ),
    (ModuleCode.PROCUREMENT, Permission.PROFIT_REVIEW_READ),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
READ_FINAL = require_any_access(
    (ModuleCode.OPERATIONS, Permission.FINAL_SELECTION_READ),
    (ModuleCode.PROCUREMENT, Permission.FINAL_SELECTION_READ),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
READ_LISTING_COPY = require_any_access(
    (ModuleCode.OPERATIONS, Permission.LISTING_COPY_READ),
    (ModuleCode.ADMIN, Permission.LISTING_COPY_READ),
)
MANAGE_FINAL = require_any_access(
    (ModuleCode.OPERATIONS, Permission.FINAL_SELECTION_MANAGE),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)
MANAGE_COMPETITORS = require_any_access(
    (ModuleCode.OPERATIONS, Permission.COMPETITOR_REFERENCE_MANAGE),
    (ModuleCode.ADMIN, Permission.ALL_BUSINESS_READ),
)


def get_selection_service(request: Request) -> SelectionService:
    return cast(SelectionService, request.app.state.selection_service)


@router.get("", response_model=SelectionListResponse)
async def list_records(
    principal: Annotated[Principal, Depends(READ_SELECTION)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> SelectionListResponse:
    return await service.list_records(principal)


@router.get("/{selection_id}", response_model=SelectionRecordResponse)
async def get_record(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_SELECTION)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> SelectionRecordResponse:
    return await service.get_record(principal, selection_id)


@router.get("/{selection_id}/quotation", response_model=QuotationResponse)
async def get_quotation(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_QUOTATION)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> QuotationResponse:
    return await service.get_quotation(principal, selection_id)


@router.put("/{selection_id}/quotation", response_model=QuotationResponse)
async def save_quotation(
    selection_id: UUID,
    payload: QuotationUpsertRequest,
    request: Request,
    principal: Annotated[Principal, Depends(MANAGE_QUOTATION)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> QuotationResponse:
    return await service.save_quotation(
        principal, selection_id, payload, getattr(request.state, "trace_id", None)
    )


@router.get("/{selection_id}/profit-review", response_model=ProfitReviewResponse)
async def get_profit_review(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_PROFIT)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> ProfitReviewResponse:
    return await service.get_profit_review(principal, selection_id)


@router.get("/{selection_id}/final-selection", response_model=FinalSelectionResponse)
async def get_final_selection(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_FINAL)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> FinalSelectionResponse:
    return await service.get_final_selection(principal, selection_id)


@router.put("/{selection_id}/final-selection", response_model=FinalSelectionResponse)
async def save_final_selection(
    selection_id: UUID,
    payload: FinalSelectionUpsertRequest,
    request: Request,
    principal: Annotated[Principal, Depends(MANAGE_FINAL)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> FinalSelectionResponse:
    return await service.save_final_selection(
        principal, selection_id, payload, getattr(request.state, "trace_id", None)
    )


@router.get("/{selection_id}/competitors", response_model=CompetitorListResponse)
async def get_competitors(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_LISTING_COPY)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> CompetitorListResponse:
    return await service.get_competitors(principal, selection_id)


@router.put("/{selection_id}/competitors", response_model=CompetitorListResponse)
async def save_competitors(
    selection_id: UUID,
    payload: CompetitorUpsertRequest,
    request: Request,
    principal: Annotated[Principal, Depends(MANAGE_COMPETITORS)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> CompetitorListResponse:
    return await service.save_competitors(
        principal, selection_id, payload, getattr(request.state, "trace_id", None)
    )


@router.get("/{selection_id}/ai-tasks", response_model=AiTaskListResponse)
async def list_ai_tasks(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_SELECTION)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> AiTaskListResponse:
    return await service.list_ai_tasks(principal, selection_id)


@router.get("/{selection_id}/listing-draft", response_model=ListingDraftResponse)
async def get_listing_draft(
    selection_id: UUID,
    principal: Annotated[Principal, Depends(READ_LISTING_COPY)],
    service: Annotated[SelectionService, Depends(get_selection_service)],
) -> ListingDraftResponse:
    return await service.get_listing_draft(principal, selection_id)
