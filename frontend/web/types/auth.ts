export type ModuleCode = "operations" | "procurement" | "creative" | "admin";
export type RoleName = ModuleCode;

export type Permission =
  | "operations.dashboard.read" | "selection.read" | "selection.create"
  | "profit_review.read" | "final_selection.read" | "final_selection.manage" | "competitor_reference.manage"
  | "project.read_assigned" | "workflow.read_assigned"
  | "listing_copy.read" | "listing_copy.generate" | "listing_copy.edit" | "listing_copy.review" | "listing_copy.history.read"
  | "ai_feedback.create_own" | "procurement.dashboard.read" | "quote.read" | "quote.manage"
  | "purchase_request.read" | "purchase_request.manage" | "fulfillment.read"
  | "creative.dashboard.read" | "content_task.read_assigned" | "asset.read" | "asset.create"
  | "asset.version.create" | "generation.request" | "review_comment.read"
  | "admin.dashboard.read" | "user.manage" | "role.manage" | "all_business.read"
  | "task.read_all" | "error.read" | "ai_feedback.read_all" | "audit_log.read"
  | "capability.read" | "system_health.read" | "store.read" | "store.manage";

export interface AccessContext {
  user: { user_id: string; username: string; display_name: string };
  roles: RoleName[];
  modules: ModuleCode[];
  permissions: Permission[];
  scopes: { organization_ids: string[]; team_ids: string[]; store_ids: string[] };
  default_landing: string;
  authorization_revision: number;
}

export interface Store {
  store_id: string;
  display_name: string;
  marketplace: string;
  organization_id: string;
  status: "active" | "inactive";
  credential_configured: boolean;
  revision: number;
  created_at: string;
  updated_at: string;
}

export interface NavigationItem {
  label: string;
  href: string;
  module: ModuleCode;
  permission: Permission;
  icon: "overview" | "search" | "opportunity" | "project" | "listing" | "publish" | "quote" | "request" | "spec" | "fulfillment" | "generation" | "asset" | "review" | "users" | "roles" | "tasks" | "approval" | "errors" | "feedback" | "release" | "audit" | "health";
}

export interface RouteAccessPolicy { path: string; module: ModuleCode; permission: Permission }
export type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "error";
