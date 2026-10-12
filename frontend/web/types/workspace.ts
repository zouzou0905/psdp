import type { ModuleCode } from "@/types/auth";
import type { WorkItem } from "@/types/dashboard";

export interface RoleDashboard {
  module: ModuleCode;
  title: string;
  description: string;
  scopeLabel: string;
  tasks: WorkItem[];
  approvals: WorkItem[];
  exceptions: WorkItem[];
  focus: Array<{ label: string; value: string; note: string }>;
  stages: Array<{ label: string; state: string; detail: string }>;
  dataSource: "api";
  asOf: string;
}

export type AdminErrorType = "system" | "api" | "worker" | "integration" | "ai_capability" | "external_status_unknown";
export type AdminErrorSeverity = "critical" | "error" | "warning" | "info";
export type AdminErrorStatus = "open" | "acknowledged" | "resolved";

export interface AdminErrorRecord {
  id: string;
  type: AdminErrorType;
  severity: AdminErrorSeverity;
  status: AdminErrorStatus;
  taskId: string | null;
  runId: string | null;
  actionId: string | null;
  module: string;
  summary: string;
  occurredAt: string;
  handled: boolean;
}
