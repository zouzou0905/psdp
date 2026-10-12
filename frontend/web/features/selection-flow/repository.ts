import { ApiError, createApiClient, type ApiClient } from "@/lib/api-client";
import type { AiTask, CompetitorInput, CompetitorList, FinalSelection, ListingDraft, ProfitReview, Quotation, QuotationInput, SelectionListResponse } from "./types";

async function optional<T>(request: Promise<T>): Promise<T | null> {
  try { return await request; }
  catch (cause) { if (cause instanceof ApiError && cause.status === 404) return null; throw cause; }
}

export class SelectionFlowRepository {
  constructor(private readonly client: ApiClient) {}
  list() { return this.client.get<SelectionListResponse>("/api/v1/selection-records"); }
  quotation(id: string) { return optional(this.client.get<Quotation>(`/api/v1/selection-records/${id}/quotation`)); }
  profitReview(id: string) { return optional(this.client.get<ProfitReview>(`/api/v1/selection-records/${id}/profit-review`)); }
  finalSelection(id: string) { return optional(this.client.get<FinalSelection>(`/api/v1/selection-records/${id}/final-selection`)); }
  competitors(id: string) { return optional(this.client.get<CompetitorList>(`/api/v1/selection-records/${id}/competitors`)); }
  aiTasks(id: string) { return this.client.get<{ items: AiTask[]; total: number }>(`/api/v1/selection-records/${id}/ai-tasks`); }
  listingDraft(id: string) { return optional(this.client.get<ListingDraft>(`/api/v1/selection-records/${id}/listing-draft`)); }
  saveQuotation(id: string, input: QuotationInput) { return this.client.put<Quotation, QuotationInput>(`/api/v1/selection-records/${id}/quotation`, input); }
  saveFinalSelection(id: string, input: { decision: "selected" | "rejected"; reason: string | null; expected_revision: number }) { return this.client.put<FinalSelection, typeof input>(`/api/v1/selection-records/${id}/final-selection`, input); }
  saveCompetitors(id: string, input: { competitors: CompetitorInput[]; expected_revision: number }) { return this.client.put<CompetitorList, typeof input>(`/api/v1/selection-records/${id}/competitors`, input); }
}

export const selectionFlowRepository = new SelectionFlowRepository(createApiClient());
