from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SkillExecutionStatus(StrEnum):
    REGISTERED_NOT_EXECUTABLE = "registered_not_executable"


class SkillRuleVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_key: str
    version: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SkillDependency(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    file_name: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class LaunchParameterDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value_type: Literal["string", "date", "integer", "enum"]
    required: bool
    description: str
    allowed_values: list[str] = Field(default_factory=list)


class SelectionSkillCard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_key: str
    package_name: str
    display_name: str
    description: str
    bundle_version: str
    skill_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_schema_version: str
    output_schema_version: str
    enabled: bool
    supports_new_product_discovery: bool
    requires_base_product: bool
    supported_sites: list[Literal["GB", "DE", "JP", "CA"]]
    execution_status: SkillExecutionStatus
    modes: list[str]


class SelectionSkillDetail(SelectionSkillCard):
    launch_parameters: list[LaunchParameterDefinition]
    shared_dependency_files: list[SkillDependency]
    rule_versions: list[SkillRuleVersion]
    output_schema: dict[str, Any]


class SelectionSkillListResponse(BaseModel):
    items: list[SelectionSkillCard]
    total: int


class CommonCandidateOutput(BaseModel):
    """Shared candidate contract; null remains distinct from a numeric zero."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    skill_key: str
    skill_version: str
    site: Literal["GB", "DE", "JP", "CA"]
    marketplace: str
    asin: str | None = None
    title: str
    product_url: HttpUrl | None = None
    price: Decimal | None = None
    currency: str | None = None
    monthly_sales: int | None = Field(default=None, ge=0)
    monthly_revenue: Decimal | None = None
    review_count: int | None = Field(default=None, ge=0)
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    source_as_of: datetime | None = None
    decision_scopes: dict[str, str] = Field(default_factory=dict)
    inquiry_lane: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: str | Decimal | None = None


class EvergreenExtension(BaseModel):
    evidence_months: int | None = None
    effective_months: int | None = None
    top3_month_demand_share: Decimal | None = None
    category_keyword_asin_consistency: str | None = None
    representative_asin_count: int | None = None
    evergreen_status: str | None = None
    preflight_market_definition: str | None = None
    preflight_parent_density_status: str | None = None
    market_evidence_block_id: str | None = None


class SeasonalExtension(BaseModel):
    evidence_months: int | None = None
    effective_months_per_cycle: int | None = None
    top3_month_demand_share: Decimal | None = None
    peak_start: str | None = None
    peak_end: str | None = None
    peak_date: str | None = None
    yoy_window_overlap: Decimal | None = None
    yoy_peak_shift: int | None = None
    selection_open_date: str | None = None
    selection_start_deadline_date: str | None = None
    selection_timing_stage: str | None = None
    required_launch_lead_days: int | None = None
    days_to_window_start: int | None = None
    lead_shortfall_days: int | None = None
    latest_purchase_date: str | None = None
    latest_fba_arrival_date: str | None = None
    timing_scope: str | None = None
    inventory_exit_plan_status: str | None = None


class HolidayExtension(BaseModel):
    event_name: str | None = None
    event_scope: str | None = None
    target_event_date: str | None = None
    repeat_cycles: int | None = None
    shopping_window_class: str | None = None
    shopping_window_start_date: str | None = None
    shopping_window_end_date: str | None = None
    selection_open_date: str | None = None
    selection_start_deadline_date: str | None = None
    development_completion_deadline_date: str | None = None
    holiday_window_share: Decimal | None = None
    peak_date_shift_days: int | None = None
    required_launch_lead_days: int | None = None
    development_slack_days: int | None = None
    lead_shortfall_days: int | None = None
    latest_purchase_date: str | None = None
    stop_replenishment_date: str | None = None
    inventory_exit_plan_status: str | None = None
    holiday_intent_evidence: list[str] = Field(default_factory=list)
    customization_status: str | None = None


class TrendingAccessoriesExtension(BaseModel):
    selection_lane: str | None = None
    primary_type_route_status: str | None = None
    portfolio_fit_status: str | None = None
    portfolio_exclusion_reason: str | None = None
    mother_scope: str | None = None
    main_product_asin_or_keyword: str | None = None
    mother_momentum_path: str | None = None
    accessory_evidence_path: str | None = None
    main_search_growth_ratio: Decimal | None = None
    main_sales_growth_ratio: Decimal | None = None
    trend_duration_days: int | None = None
    accessory_growth_ratio: Decimal | None = None
    compatibility_status: str | None = None
    supported_models: list[str] = Field(default_factory=list)
    ecosystem_type: str | None = None
    trademark_usage_status: str | None = None
    remaining_heat_days_low: int | None = None
    remaining_heat_days_high: int | None = None
    causal_chain_status: str | None = None


class ConsumablesMultipacksExtension(BaseModel):
    selection_mode: Literal["independent_discovery", "tag_review"]
    selection_lane: str | None = None
    selection_lane_decision: str | None = None
    buyer_segment: str | None = None
    use_context: str | None = None
    depletion_mechanism: str | None = None
    branch_mode: str | None = None
    pack_scope: str | None = None
    pack_ladder: list[str] = Field(default_factory=list)
    target_pack_tier: str | None = None
    target_pack_count: int | None = None
    pack_market_fit_status: str | None = None
    selected_launch_strategy_tags: list[str] = Field(default_factory=list)
    primary_type: str | None = None
    primary_type_validation_status: str | None = None
    consumable_status: str | None = None
    repeat_cycle_days: int | None = None
    large_pcs_status: str | None = None
    stated_piece_count: int | None = None
    effective_units: Decimal | None = None
    retail_unit_price: Decimal | None = None
    benchmark_unit_price: Decimal | None = None
    unit_value_advantage: Decimal | None = None


class ValidatedVariationsExtension(BaseModel):
    base_asin: str
    base_primary_type: str | None = None
    base_validation_status: str | None = None
    base_stability_status: str | None = None
    existing_parent_asin: str | None = None
    existing_child_count: int | None = None
    proposed_dimension: str | None = None
    proposed_child_value: str | None = None
    difference_description: str | None = None
    core_function_changed: bool | None = None
    category_theme_supported: bool | None = None
    proposed_variation_theme: str | None = None
    relationship_route: str | None = None
    relationship_decision: str | None = None
    review_policy_as_of: str | None = None
    review_sharing_expected: bool | None = None
    review_sharing_basis: str | None = None
    variant_keyword_evidence: list[str] = Field(default_factory=list)
    estimated_target_offer_monthly_sales: int | None = None
    cannibalization_rate: Decimal | None = None
    incremental_portfolio_profit: Decimal | None = None
    new_children_in_batch: int | None = None
    matrix_stage: str | None = None
    offer_decision: str | None = None


class EvergreenCandidateOutput(CommonCandidateOutput):
    extension: EvergreenExtension


class SeasonalCandidateOutput(CommonCandidateOutput):
    extension: SeasonalExtension


class HolidayCandidateOutput(CommonCandidateOutput):
    extension: HolidayExtension


class TrendingAccessoriesCandidateOutput(CommonCandidateOutput):
    extension: TrendingAccessoriesExtension


class ConsumablesMultipacksCandidateOutput(CommonCandidateOutput):
    extension: ConsumablesMultipacksExtension


class ValidatedVariationsCandidateOutput(CommonCandidateOutput):
    extension: ValidatedVariationsExtension


OUTPUT_MODELS: dict[str, type[CommonCandidateOutput]] = {
    "evergreen": EvergreenCandidateOutput,
    "seasonal": SeasonalCandidateOutput,
    "holiday": HolidayCandidateOutput,
    "trending_accessories": TrendingAccessoriesCandidateOutput,
    "consumables_multipacks": ConsumablesMultipacksCandidateOutput,
    "validated_variations": ValidatedVariationsCandidateOutput,
}
