"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertTriangle, Archive, Bell, Bot, Boxes, CheckCircle2, ChevronRight, CircleAlert, ClipboardCheck,
  FileCheck2, FileClock, FileText, Gauge, HeartPulse, History, Image, ListChecks, LogOut,
  ListTodo, Menu, PackageCheck, PackageSearch, PanelLeftClose, ReceiptText, Settings2, ShieldCheck,
  ShoppingCart, Sparkles, Truck, UserCog, Users, WandSparkles, X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { navigationFor, navigationItemForPath, moduleHome } from "@/config/access-control";
import { useAuth } from "@/components/auth/auth-provider";
import { RouteGuard } from "@/components/auth/route-guard";
import { createWorkspaceRepository } from "@/repositories/workspace-repository";
import { ApiError } from "@/lib/api-client";
import type { ModuleCode, NavigationItem } from "@/types/auth";
import type { WorkItem } from "@/types/dashboard";
import type { AdminErrorRecord, RoleDashboard } from "@/types/workspace";
import { SelectionWorkbench } from "@/features/selection-flow/selection-workbench";

const repository = createWorkspaceRepository();
const iconMap: Record<NavigationItem["icon"], typeof Gauge> = { overview: Gauge, search: PackageSearch, opportunity: Sparkles, project: Archive, listing: FileText, publish: FileCheck2, quote: ReceiptText, request: ShoppingCart, spec: PackageCheck, fulfillment: Truck, generation: WandSparkles, asset: Image, review: FileClock, users: Users, roles: UserCog, tasks: ListChecks, approval: ClipboardCheck, errors: CircleAlert, feedback: Bot, release: Settings2, audit: History, health: HeartPulse };
const moduleLabels: Record<ModuleCode, string> = { operations: "运营工作台", procurement: "采购工具台", creative: "美工工作台", admin: "管理工作台" };

function WorkspaceState({ kind, retry }: { kind: "loading" | "error" | "forbidden"; retry?: () => void }) {
  const loading = kind === "loading";
  return <div className="workspace-state">{loading ? <span className="spinner" /> : <CircleAlert />}<strong>{loading ? "正在加载账号范围数据" : kind === "forbidden" ? "没有数据访问权限" : "工作台数据加载失败"}</strong><p>{loading ? "正在获取与后端授权范围匹配的任务…" : kind === "forbidden" ? "后端拒绝了本次读取，旧数据已清除。" : "后端服务或数据库暂不可用，请检查后重试。"}</p>{retry ? <button className="primary-button" onClick={retry}>重新加载</button> : null}</div>;
}

function RoleSidebar({ module, pathname, mobileOpen, onClose }: { module: ModuleCode; pathname: string; mobileOpen: boolean; onClose: () => void }) {
  const { user } = useAuth();
  if (!user) return null;
  return <><button className={`mobile-scrim ${mobileOpen ? "visible" : ""}`} onClick={onClose} aria-label="关闭导航遮罩" /><aside className={`sidebar role-sidebar ${mobileOpen ? "open" : ""}`}><div className="brand"><span className="brand-symbol"><Boxes /></span><span className="brand-title">AI 商品运营中台</span><button onClick={onClose} aria-label="关闭导航"><PanelLeftClose /></button></div><div className="role-context"><small>当前板块</small><strong>{moduleLabels[module]}</strong><span>授权版本 {user.authorization_revision}</span></div><nav aria-label="主导航">{navigationFor(user).map((item) => { const Icon = iconMap[item.icon]; return <Link key={item.href} href={item.href} className={pathname === item.href ? "active" : ""} onClick={onClose}><Icon /><span>{item.label}</span></Link>; })}</nav><div className="sidebar-boundary"><ShieldCheck /><p>菜单展示用于改善使用体验<br />正式权限由后端执行</p></div></aside></>;
}

function RoleTopbar({ module, pathname, onMenu }: { module: ModuleCode; pathname: string; onMenu: () => void }) {
  const router = useRouter();
  const { user, stores, selectedStoreId, selectStore, logout } = useAuth();
  if (!user) return null;
  const currentItem = navigationItemForPath(pathname);
  return <header className="topbar role-topbar"><button className="icon-button mobile-menu" onClick={onMenu} aria-label="打开导航"><Menu /></button><div className="workspace-breadcrumb"><Boxes /><span>{moduleLabels[module]}</span>{currentItem && currentItem.href !== moduleHome[module] ? <><ChevronRight /><strong>{currentItem.label}</strong></> : null}</div><div className="topbar-actions">{(module === "operations" || module === "procurement") && stores.length ? <label className="store-switcher"><span>授权店铺</span><select aria-label="授权店铺" value={selectedStoreId ?? ""} onChange={(event) => selectStore(event.target.value)}>{stores.map((store) => <option key={store.store_id} value={store.store_id}>{store.display_name} · {store.marketplace}</option>)}</select></label> : null}<button className="topbar-utility" disabled title="统一任务入口等待后端契约"><ListTodo /><span>全局任务</span></button><button className="topbar-utility" disabled title="统一异常入口等待后端契约"><Bell /><span>异常中心</span></button><div className="user-block"><span className="avatar">{user.user.display_name.slice(0, 1)}</span><span><strong>{user.user.display_name}</strong><small>{user.user.username}</small></span></div><button className="logout-button" onClick={async () => { await logout(); router.replace("/login"); }}><LogOut /><span>退出</span></button></div></header>;
}

function TaskList({ items, emptyText, onInspect }: { items: WorkItem[]; emptyText: string; onInspect: (item: WorkItem) => void }) {
  if (!items.length) return <div className="empty-state"><CheckCircle2 /><strong>{emptyText}</strong><span>当前权限范围内没有需要处理的记录。</span></div>;
  return <div className="role-task-list">{items.map((item) => <button key={item.id} onClick={() => onInspect(item)}><span className={`priority priority-${item.priority}`}>{item.priority === "high" ? "高" : item.priority === "medium" ? "中" : "低"}</span><div><strong>{item.title}</strong><small>{item.project} · {item.id}</small></div><span className={`status-tag status-${item.status}`}><i />{item.status === "running" ? "进行中" : item.status === "pending" ? "待处理" : item.status === "failed" ? "失败" : item.status === "blocked" ? "已阻塞" : "待核对"}</span><ChevronRight /></button>)}</div>;
}

function RoleHome({ data, onInspect }: { data: RoleDashboard; onInspect: (item: WorkItem) => void }) {
  const [tab, setTab] = useState<"tasks" | "approvals" | "exceptions">("tasks");
  const items = tab === "tasks" ? data.tasks : tab === "approvals" ? data.approvals : data.exceptions;
  return <><div className="page-heading"><div><h1>{data.title}</h1><p>{data.description}</p></div><span className="scope-label">{data.scopeLabel}</span></div><div className="source-notice api"><CircleAlert /><strong>后端数据 · 当前授权范围</strong><span>数据由对应板块工作台接口返回。</span><i /><ShieldCheck /><span>正式读取与操作仍需后端授权。</span></div><section className="role-focus-grid">{data.focus.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</section><div className="role-dashboard-grid"><section className="panel role-queue"><div className="panel-heading"><div><h2>我的工作队列</h2><p>只显示当前账号需要处理的事项</p></div><span className="as-of">更新于 {data.asOf}</span></div><div className="tabs role-tabs"><button className={tab === "tasks" ? "active" : ""} onClick={() => setTab("tasks")}>待办任务 <span>{data.tasks.length}</span></button><button className={tab === "approvals" ? "active" : ""} onClick={() => setTab("approvals")}>待审批 <span>{data.approvals.length}</span></button><button className={tab === "exceptions" ? "active" : ""} onClick={() => setTab("exceptions")}>异常 <span>{data.exceptions.length}</span></button></div><TaskList items={items} emptyText="当前队列已处理完成" onInspect={onInspect} /></section><section className="panel role-progress"><div className="panel-heading"><div><h2>板块流程状态</h2><p>按授权边界展示必要信息</p></div></div><div>{data.stages.map((stage, index) => <div className="role-stage" key={stage.label}><span>{index + 1}</span><div><strong>{stage.label}</strong><small>{stage.detail}</small></div><em>{stage.state}</em></div>)}</div></section></div></>;
}

const errorTypeLabel: Record<AdminErrorRecord["type"], string> = { system: "系统错误", api: "API 错误", worker: "Worker 任务错误", integration: "外部系统错误", ai_capability: "AI 能力错误", external_status_unknown: "外部状态未知" };

function AdminErrorCenter() {
  const [records, setRecords] = useState<AdminErrorRecord[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [type, setType] = useState("all");
  useEffect(() => { repository.getAdminErrors().then(setRecords).catch(() => setLoadError(true)); }, []);
  const filtered = useMemo(() => records?.filter((item) => type === "all" || item.type === type) ?? [], [records, type]);
  if (loadError) return <WorkspaceState kind="error" retry={() => window.location.reload()} />;
  if (!records) return <WorkspaceState kind="loading" />;
  return <><div className="page-heading"><div><h1>管理员错误中心</h1><p>统一查看系统、外部执行、AI 错误与结果反馈。</p></div><span className="scope-label">管理员专属 · 脱敏视图</span></div><div className="source-notice demo"><AlertTriangle /><strong>敏感字段已排除</strong><span>不展示密码、Token、API Key、数据库连接串或完整敏感请求体。</span></div><section className="panel admin-error-panel"><div className="panel-heading"><div><h2>错误与反馈记录</h2><p>关联 task_id、run_id 与 action_id 以支持追踪</p></div><select aria-label="错误类型筛选" value={type} onChange={(event) => setType(event.target.value)}><option value="all">全部类型</option>{Object.entries(errorTypeLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="table-wrap"><table><thead><tr><th>ID / 类型</th><th>严重程度</th><th>状态</th><th>任务关联</th><th>能力或模块</th><th>摘要</th><th>发生时间</th><th>已处理</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td><strong>{item.id}</strong><small className="row-id">{errorTypeLabel[item.type]}</small></td><td><span className={`severity severity-${item.severity}`}>{item.severity}</span></td><td>{item.status}</td><td className="trace-cell"><span>task: {item.taskId ?? "—"}</span><span>run: {item.runId ?? "—"}</span><span>action: {item.actionId ?? "—"}</span></td><td>{item.module}</td><td className="summary-cell">{item.summary}</td><td>{item.occurredAt}</td><td>{item.handled ? "是" : "否"}</td></tr>)}</tbody></table></div></section></>;
}

function ModulePlaceholder({ pathname, module }: { pathname: string; module: ModuleCode }) {
  const { user } = useAuth();
  if (!user) return null;
  const item = navigationItemForPath(pathname);
  if (!item) return null;
  const Icon = iconMap[item.icon];
  return <><div className="page-heading module-title"><div className="module-icon"><Icon /></div><div><h1>{item.label}</h1><p>此模块已纳入当前账号的信息架构，详细业务能力等待后端契约接入。</p></div></div><section className="panel placeholder-panel"><div className="placeholder-symbol"><Icon /></div><h2>{item.label}工作区</h2><p>{module === "admin" ? "管理员可查看获准范围，正式操作仍需后端重新授权。" : "这里只会显示当前账号和负责范围内的数据。"}</p><div className="human-boundary"><ShieldCheck /><div><h3>访问边界</h3><p>当前页面已通过统一 RouteAccessPolicy 检查；前端守卫不替代后端权限校验。</p></div></div></section></>;
}

function TaskDrawer({ task, onClose }: { task: WorkItem | null; onClose: () => void }) {
  if (!task) return null;
  return <><button className="drawer-scrim" onClick={onClose} aria-label="关闭任务详情" /><aside className="detail-drawer" aria-label="任务详情"><div className="drawer-header"><div><small>岗位任务详情</small><h2>{task.title}</h2></div><button className="icon-button" onClick={onClose} aria-label="关闭"><X /></button></div><div className="drawer-content"><p className="drawer-summary">{task.detail}</p><section><h3>追踪信息</h3><dl><div><dt>task_id</dt><dd>{task.id}</dd></div><div><dt>run_id</dt><dd>{task.runId ?? "缺失"}</dd></div><div><dt>输入版本</dt><dd>{task.specVersion ?? "不可用"}</dd></div><div><dt>所属项目</dt><dd>{task.project}</dd></div></dl></section><section className="human-boundary"><ShieldCheck /><div><h3>后端授权边界</h3><p>查看详情不代表拥有审批或执行权限；高风险动作必须由后端再次授权。</p></div></section></div><div className="drawer-footer"><button className="secondary-button" onClick={onClose}>关闭</button></div></aside></>;
}

function WorkspaceContent({ module, pathname }: { module: ModuleCode; pathname: string }) {
  const { user } = useAuth();
  const [data, setData] = useState<RoleDashboard | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [drawerTask, setDrawerTask] = useState<WorkItem | null>(null);
  const [mobileNav, setMobileNav] = useState(false);
  const isHome = pathname === moduleHome[module];
  useEffect(() => {
    if (module === "operations" || module === "procurement") return;
    let active = true;
    const timer = window.setTimeout(() => {
      setData(null); setLoadError(false); setForbidden(false);
      repository.getDashboard(module).then((next) => { if (active) setData(next); }).catch((cause) => {
        if (!active) return;
        setData(null);
        if (cause instanceof ApiError && cause.status === 403) setForbidden(true); else setLoadError(true);
      });
    }, 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [module]);
  const flowWorkspace = module === "operations" || module === "procurement";
  const accessKey = user ? `${user.user.user_id}:${user.authorization_revision}` : "anonymous";
  return <div className="app-shell"><RoleSidebar module={module} pathname={pathname} mobileOpen={mobileNav} onClose={() => setMobileNav(false)} /><div className="workspace"><RoleTopbar module={module} pathname={pathname} onMenu={() => setMobileNav(true)} /><main className="main-content">{flowWorkspace ? <SelectionWorkbench key={accessKey} module={module} pathname={pathname} /> : forbidden ? <WorkspaceState kind="forbidden" /> : loadError ? <WorkspaceState kind="error" retry={() => window.location.reload()} /> : !data ? <WorkspaceState kind="loading" /> : pathname === "/admin/errors" ? <AdminErrorCenter /> : isHome ? <RoleHome data={data} onInspect={setDrawerTask} /> : <ModulePlaceholder pathname={pathname} module={module} />}</main></div><TaskDrawer task={drawerTask} onClose={() => setDrawerTask(null)} /></div>;
}

export function RoleWorkspace({ module, pathname }: { module: ModuleCode; pathname: string }) {
  return <RouteGuard pathname={pathname}><WorkspaceContent module={module} pathname={pathname} /></RouteGuard>;
}
