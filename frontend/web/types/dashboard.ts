export type ValueStatus = "missing" | "zero" | "estimated" | "failed" | "unavailable" | "confirmed";
export type TaskStatus = "running" | "pending" | "blocked" | "failed" | "succeeded" | "waiting_external";

export interface WorkspaceUser {
  name: string;
  role: string;
  team: string;
}

export interface WorkItem {
  id: string;
  title: string;
  project: string;
  type: string;
  priority: "high" | "medium" | "low";
  dueAt: string;
  status: TaskStatus;
  runId: string | null;
  specVersion: string | null;
  detail: string;
}

export interface OperatingProject {
  id: string;
  name: string;
  owner: string;
  category: string;
  stage: string;
  progress: string;
  risk: "normal" | "attention" | "exception" | "paused";
  updatedAt: string;
}

export interface FlowStage {
  name: string;
  completed: number;
  total: number;
  status: ValueStatus;
}

export interface TaskRun {
  id: string;
  task: string;
  time: string;
  status: TaskStatus;
}

export interface DashboardSummary {
  user: WorkspaceUser;
  workItems: WorkItem[];
  approvals: WorkItem[];
  exceptions: WorkItem[];
  projects: OperatingProject[];
  flow: FlowStage[];
  recentRuns: TaskRun[];
  dataSource: "api" | "demo";
  asOf: string;
}
