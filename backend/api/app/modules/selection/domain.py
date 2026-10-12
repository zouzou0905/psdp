from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SelectionStage(StrEnum):
    SOURCED = "sourced"
    QUOTED = "quoted"
    PROFIT_REVIEWED = "profit_reviewed"
    FINAL_SELECTED = "final_selected"
    FINAL_REJECTED = "final_rejected"


class ValueStatus(StrEnum):
    MISSING = "missing"
    ZERO = "zero"
    ESTIMATED = "estimated"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    CONFIRMED = "confirmed"


class FinalDecision(StrEnum):
    SELECTED = "selected"
    REJECTED = "rejected"


class AiTaskType(StrEnum):
    INITIAL_SELECTION = "initial_selection"
    PROFIT_REVIEW = "profit_review"
    LISTING_DRAFT = "listing_draft"


class AiTaskStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SelectionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    selection_id: UUID
    store_id: str
    marketplace: str
    product_name: str
    source_type: str
    source_ref: str | None
    source_snapshot_ref: str | None
    source_version: str
    owner_id: UUID | None
    stage: SelectionStage
    revision: int
    created_at: datetime
    updated_at: datetime


class SelectionListResponse(BaseModel):
    items: list[SelectionRecordResponse]
    total: int = Field(ge=0)


class QuotationUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_name: str = Field(min_length=1, max_length=255)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    value_status: ValueStatus
    moq: int | None = Field(default=None, ge=1)
    lead_time_days: int | None = Field(default=None, ge=0)
    freight_per_unit: Decimal | None = Field(default=None, ge=0)
    other_cost_per_unit: Decimal | None = Field(default=None, ge=0)
    target_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)
    expected_revision: int = Field(ge=1)


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quotation_id: UUID
    selection_id: UUID
    version: int
    supplier_name: str
    unit_cost: Decimal | None
    currency: str
    value_status: ValueStatus
    moq: int | None
    lead_time_days: int | None
    freight_per_unit: Decimal | None
    other_cost_per_unit: Decimal | None
    target_price: Decimal | None
    notes: str | None
    recorded_by: UUID
    created_at: datetime


class ProfitReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profit_review_id: UUID
    selection_id: UUID
    version: int
    quotation_version: int
    margin_amount: Decimal | None
    margin_rate: Decimal | None
    currency: str | None
    value_status: ValueStatus
    recommendation: str
    explanation: str | None
    missing_inputs: list[str]
    task_id: str
    run_id: str | None
    created_at: datetime


class FinalSelectionUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: FinalDecision
    reason: str | None = Field(default=None, max_length=2000)
    expected_revision: int = Field(ge=1)


class FinalSelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    final_selection_id: UUID
    selection_id: UUID
    version: int
    profit_review_version: int
    decision: FinalDecision
    reason: str | None
    decided_by: UUID
    created_at: datetime


class CompetitorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=1000)
    bullets: list[str] = Field(min_length=5, max_length=5)

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, value: list[str]) -> list[str]:
        if any(not bullet.strip() or len(bullet) > 1000 for bullet in value):
            raise ValueError("Each bullet must contain 1 to 1000 characters")
        return value


class CompetitorUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competitors: list[CompetitorInput] = Field(min_length=3, max_length=3)
    expected_revision: int = Field(ge=1)


class CompetitorResponse(CompetitorInput):
    model_config = ConfigDict(from_attributes=True)

    competitor_id: UUID
    position: int


class CompetitorListResponse(BaseModel):
    selection_id: UUID
    final_version: int
    competitors: list[CompetitorResponse]
    revision: int


class AiTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    selection_id: UUID
    task_type: AiTaskType
    input_version: str
    status: AiTaskStatus
    run_id: str | None
    result_version: str | None
    error_code: str | None
    created_at: datetime
    updated_at: datetime


class AiTaskListResponse(BaseModel):
    items: list[AiTaskResponse]
    total: int


class ListingDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    listing_draft_id: UUID
    selection_id: UUID
    version: int
    final_version: int
    title: str
    bullets: list[str]
    status: str
    task_id: str
    run_id: str | None
    created_at: datetime
