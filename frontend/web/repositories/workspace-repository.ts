import { createApiClient, type ApiClient } from "@/lib/api-client";
import type { ModuleCode } from "@/types/auth";
import type { TaskStatus, WorkItem } from "@/types/dashboard";
import type { AdminErrorRecord, AdminErrorSeverity, AdminErrorStatus, AdminErrorType, RoleDashboard } from "@/types/workspace";

interface WorkspaceRecord { record_id: string; store_id: string | null; record_type: string; title: string; status: string; updated_at: string; summary: Record<string, unknown> }
interface DashboardResponse {
  workspace: ModuleCode; generated_at: string; data_status: string; disclaimer: string;
  counts: Record<string, number>; alerts: string[];
  work_items?: WorkspaceRecord[]; projects?: WorkspaceRecord[]; purchase_requests?: WorkspaceRecord[]; content_tasks?: WorkspaceRecord[]; readable_modules?: string[];
}
interface ErrorRecord {
  error_id: string; category: AdminErrorType; severity: AdminErrorSeverity; status: AdminErrorStatus; module: string;
  task_id: string | null; run_id: string | null; action_id: string | null; summary: string; occurred_at: string; resolved_at: string | null;
}

const presentation: Record<ModuleCode, { title: string; description: string; focus: string[]; stages: string[] }> = {
  operations: { title: "运营总览", description: "只显示账号授权范围内的商品、项目与运营任务。", focus: ["待办任务", "经营项目", "异常提醒"], stages: ["商品机会", "经营项目", "Listing 与上架"] },
  procurement: { title: "采购总览", description: "处理已授权采购任务、报价与履约异常。", focus: ["待处理申请", "开放报价", "履约异常"], stages: ["询价与报价", "规格与申请", "交期与履约"] },
  creative: { title: "美工总览", description: "处理分配给当前账号的内容任务、素材和审核意见。", focus: ["待制作任务", "审核中素材", "生成失败"], stages: ["内容任务", "素材制作", "审核与交付"] },
  admin: { title: "全局业务总览", description: "查看账号获准访问的业务板块和系统治理状态。", focus: ["未处理错误", "待处理 AI 反馈", "审计事件"], stages: ["业务运行", "错误与反馈", "审计与健康"] },
};

function mapStatus(status: string): TaskStatus {
  if (["running", "in_progress"].includes(status)) return "running";
  if (["failed", "error"].includes(status)) return "failed";
  if (["blocked", "overdue"].includes(status)) return "blocked";
  return "pending";
}
function mapItem(item: WorkspaceRecord, type = "任务"): WorkItem {
  const summary = typeof item.summary.description === "string" ? item.summary.description : "后端尚未提供更多详情。";
  return { id: item.record_id, title: item.title, project: item.store_id ? `店铺 ${item.store_id}` : "当前授权范围", type, priority: ["failed", "blocked", "overdue"].includes(item.status) ? "high" : "medium", dueAt: new Date(item.updated_at).toLocaleString("zh-CN", { hour12: false }), status: mapStatus(item.status), runId: null, specVersion: null, detail: summary };
}

export interface WorkspaceRepository { getDashboard(module: ModuleCode): Promise<RoleDashboard>; getAdminErrors(): Promise<AdminErrorRecord[]> }
export class ApiWorkspaceRepository implements WorkspaceRepository {
  constructor(private readonly client: ApiClient) {}
  async getDashboard(module: ModuleCode): Promise<RoleDashboard> {
    const response = await this.client.get<DashboardResponse>(`/api/v1/${module}/dashboard`);
    const records = response.work_items ?? response.purchase_requests ?? response.content_tasks ?? [];
    const values = Object.values(response.counts);
    const labels = presentation[module];
    const alerts = response.alerts.map((title, index) => mapItem({ record_id: `alert-${index}`, store_id: null, record_type: "alert", title, status: "blocked", updated_at: response.generated_at, summary: {} }, "异常"));
    return {
      module, title: labels.title, description: labels.description,
      scopeLabel: module === "operations" ? "后端授权店铺范围" : "后端账号授权范围",
      tasks: records.map((item) => mapItem(item)), approvals: [], exceptions: alerts,
      focus: labels.focus.map((label, index) => ({ label, value: String(values[index] ?? 0), note: "后端确认值" })),
      stages: labels.stages.map((label, index) => ({ label, state: index === 0 ? "处理中" : "待推进", detail: "仅展示当前账号可见数据" })),
      dataSource: "api", asOf: new Date(response.generated_at).toLocaleString("zh-CN", { hour12: false }),
    };
  }
  async getAdminErrors(): Promise<AdminErrorRecord[]> {
    const response = await this.client.get<{ items: ErrorRecord[]; total: number }>("/api/v1/admin/errors");
    return response.items.map((item) => ({ id: item.error_id, type: item.category, severity: item.severity, status: item.status, taskId: item.task_id, runId: item.run_id, actionId: item.action_id, module: item.module, summary: item.summary, occurredAt: new Date(item.occurred_at).toLocaleString("zh-CN", { hour12: false }), handled: item.status === "resolved" }));
  }
}
export function createWorkspaceRepository(): WorkspaceRepository { return new ApiWorkspaceRepository(createApiClient()); }
