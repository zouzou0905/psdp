import type { AccessContext, ModuleCode, NavigationItem, Permission, RouteAccessPolicy } from "@/types/auth";

export const moduleHome: Record<ModuleCode, string> = { operations: "/operations", procurement: "/procurement", creative: "/creative", admin: "/admin" };
const navigation: Record<ModuleCode, NavigationItem[]> = {
  operations: [
    { label: "运营工作台", href: "/operations", module: "operations", permission: "operations.dashboard.read", icon: "overview" },
    { label: "利润选品表", href: "/operations/profit-selections", module: "operations", permission: "profit_review.read", icon: "opportunity" },
    { label: "人工复选", href: "/operations/final-selection", module: "operations", permission: "final_selection.read", icon: "project" },
    { label: "竞品资料", href: "/operations/competitors", module: "operations", permission: "final_selection.read", icon: "search" },
    { label: "Listing 文案", href: "/operations/listings", module: "operations", permission: "listing_copy.read", icon: "listing" },
  ],
  procurement: [
    { label: "采购工具台", href: "/procurement", module: "procurement", permission: "procurement.dashboard.read", icon: "overview" },
    { label: "AI 选品", href: "/procurement/selection", module: "procurement", permission: "selection.read", icon: "search" },
    { label: "采购询价", href: "/procurement/quotes", module: "procurement", permission: "quote.read", icon: "quote" },
    { label: "利润复核", href: "/procurement/profit-reviews", module: "procurement", permission: "profit_review.read", icon: "spec" },
  ],
  creative: [
    { label: "美工总览", href: "/creative", module: "creative", permission: "creative.dashboard.read", icon: "overview" },
    { label: "AI 生图", href: "/creative/generation", module: "creative", permission: "generation.request", icon: "generation" },
    { label: "图片 / 视频素材", href: "/creative/assets", module: "creative", permission: "asset.read", icon: "asset" },
    { label: "素材版本", href: "/creative/versions", module: "creative", permission: "asset.read", icon: "spec" },
    { label: "修改与退回", href: "/creative/reviews", module: "creative", permission: "review_comment.read", icon: "review" },
  ],
  admin: [
    { label: "全局业务总览", href: "/admin", module: "admin", permission: "admin.dashboard.read", icon: "overview" },
    { label: "用户管理", href: "/admin/users", module: "admin", permission: "user.manage", icon: "users" },
    { label: "角色和权限", href: "/admin/roles", module: "admin", permission: "role.manage", icon: "roles" },
    { label: "全部任务", href: "/admin/tasks", module: "admin", permission: "task.read_all", icon: "tasks" },
    { label: "错误中心", href: "/admin/errors", module: "admin", permission: "error.read", icon: "errors" },
    { label: "AI 反馈", href: "/admin/ai-feedback", module: "admin", permission: "ai_feedback.read_all", icon: "feedback" },
    { label: "AI 能力版本", href: "/admin/ai-releases", module: "admin", permission: "capability.read", icon: "release" },
    { label: "审计日志", href: "/admin/audit-logs", module: "admin", permission: "audit_log.read", icon: "audit" },
    { label: "系统健康", href: "/admin/health", module: "admin", permission: "system_health.read", icon: "health" },
  ],
};

export const routePolicies: RouteAccessPolicy[] = Object.values(navigation).flat().map(({ href, module, permission }) => ({ path: href, module, permission }));
export function can(user: AccessContext | null, permission: Permission): boolean { return Boolean(user?.permissions.includes(permission)); }
export function navigationFor(user: AccessContext): NavigationItem[] { return user.modules.flatMap((module) => navigation[module] ?? []).filter((item) => can(user, item.permission)); }
export function navigationItemForPath(pathname: string): NavigationItem | undefined { return Object.values(navigation).flat().find((item) => item.href === pathname); }
export function policyForPath(pathname: string): RouteAccessPolicy | undefined { return routePolicies.find((item) => item.path === pathname); }
export function canAccessPath(user: AccessContext, pathname: string): boolean { const policy = policyForPath(pathname); return Boolean(policy && user.modules.includes(policy.module) && can(user, policy.permission)); }
export function isModule(value: string): value is ModuleCode { return value in moduleHome; }
