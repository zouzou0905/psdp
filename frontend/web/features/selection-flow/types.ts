export type ValueStatus = "missing" | "zero" | "estimated" | "failed" | "unavailable" | "confirmed";
export type SelectionStage = "sourced" | "quoted" | "profit_reviewed" | "final_selected" | "final_rejected";
export type AiTaskStatus = "planned" | "queued" | "running" | "succeeded" | "failed" | "cancelled";
export type AiTaskType = "initial_selection" | "profit_review" | "listing_draft";

export interface SelectionRecord {
  selection_id: string; store_id: string; marketplace: string; product_name: string;
  source_type: string; source_ref: string | null; source_snapshot_ref: string | null;
  source_version: string; owner_id: string | null; stage: SelectionStage; revision: number;
  created_at: string; updated_at: string;
}
export interface SelectionListResponse { items: SelectionRecord[]; total: number }
export interface Quotation {
  quotation_id: string; selection_id: string; version: number; supplier_name: string;
  unit_cost: string | null; currency: string; value_status: ValueStatus; moq: number | null;
  lead_time_days: number | null; freight_per_unit: string | null; other_cost_per_unit: string | null;
  target_price: string | null; notes: string | null; recorded_by: string; created_at: string;
}
export interface QuotationInput {
  supplier_name: string; unit_cost?: string | null; currency: string; value_status: ValueStatus;
  moq?: number | null; lead_time_days?: number | null; freight_per_unit?: string | null;
  other_cost_per_unit?: string | null; target_price?: string | null; notes?: string | null; expected_revision: number;
}
export interface ProfitReview {
  profit_review_id: string; selection_id: string; version: number; quotation_version: number;
  margin_amount: string | null; margin_rate: string | null; currency: string | null; value_status: ValueStatus;
  recommendation: string; explanation: string | null; missing_inputs: string[]; task_id: string;
  run_id: string | null; created_at: string;
}
export interface FinalSelection {
  final_selection_id: string; selection_id: string; version: number; profit_review_version: number;
  decision: "selected" | "rejected"; reason: string | null; decided_by: string; created_at: string;
}
export interface CompetitorInput { title: string; bullets: string[] }
export interface Competitor extends CompetitorInput { competitor_id: string; position: number }
export interface CompetitorList { selection_id: string; final_version: number; competitors: Competitor[]; revision: number }
export interface AiTask {
  task_id: string; selection_id: string; task_type: AiTaskType; input_version: string; status: AiTaskStatus;
  run_id: string | null; result_version: string | null; error_code: string | null; created_at: string; updated_at: string;
}
export interface ListingDraft {
  listing_draft_id: string; selection_id: string; version: number; final_version: number; title: string;
  bullets: string[]; status: string; task_id: string; run_id: string | null; created_at: string;
}
