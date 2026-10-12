"use client";

import Link from "next/link";
import { AlertTriangle, Bot, CheckCircle2, ChevronRight, CircleHelp, FilePenLine, Info, ListFilter, RefreshCw, Save, Search, Sparkles, TableProperties } from "lucide-react";
import { useCallback, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/auth-provider";
import { can } from "@/config/access-control";
import { ApiError } from "@/lib/api-client";
import { selectionFlowRepository as repository } from "./repository";
import type { AiTask, CompetitorInput, CompetitorList, FinalSelection, ListingDraft, ProfitReview, Quotation, QuotationInput, SelectionRecord, ValueStatus } from "./types";
import type { ModuleCode, Permission, Store } from "@/types/auth";

type FlowView = "overview" | "ai-selection" | "quotation" | "profit" | "final" | "competitors" | "listing";
type Detail = { quotation?: Quotation | null; profit?: ProfitReview | null; final?: FinalSelection | null; competitors?: CompetitorList | null; tasks?: AiTask[]; listing?: ListingDraft | null };

const viewByPath: Record<string, FlowView> = {
  "/procurement": "overview", "/procurement/selection": "ai-selection", "/procurement/quotes": "quotation", "/procurement/profit-reviews": "profit",
  "/operations": "overview", "/operations/profit-selections": "profit", "/operations/final-selection": "final", "/operations/competitors": "competitors", "/operations/listings": "listing",
};
const viewCopy: Record<FlowView, { title: string; description: string }> = {
  overview: { title: "六步业务工作台", description: "查看选品来源、登记询价并跟踪利润复核结果。" },
  "ai-selection": { title: "AI 选品", description: "查看 DeepSeek、用户 Skill 与 Sorftime MCP 的任务边界和选品结果。" },
  quotation: { title: "采购询价", description: "采购人员查看选品记录并人工登记、修订询价信息。" },
  profit: { title: "利润复核", description: "查看程序金额结果、AI 复核依据以及缺失或估算数据。" },
  final: { title: "人工复选", description: "运营人工选择或淘汰利润候选，形成可追溯的最终选品版本。" },
  competitors: { title: "竞品资料", description: "为已选商品维护恰好 3 条竞品，每条包含标题和 5 条要点。" },
  listing: { title: "Listing 文案", description: "运营按授权店铺查看最终选品关联的标题和五点草稿版本。" },
};
const stageLabel: Record<SelectionRecord["stage"], string> = { sourced: "已初选", quoted: "已询价", profit_reviewed: "已复核", final_selected: "已选中", final_rejected: "已淘汰" };
const valueLabel: Record<ValueStatus, string> = { missing: "缺失", zero: "零值", estimated: "估算", failed: "失败", unavailable: "不可用", confirmed: "已确认" };
const taskLabel: Record<AiTask["task_type"], string> = { initial_selection: "AI 初步选品", profit_review: "AI 利润复核", listing_draft: "Listing 草稿" };
const taskStatusLabel: Record<AiTask["status"], string> = { planned: "未配置", queued: "排队中", running: "运行中", succeeded: "已完成", failed: "失败", cancelled: "已取消" };

function formatTime(value: string) { return new Date(value).toLocaleString("zh-CN", { hour12: false }); }
function optionalNumber(value: FormDataEntryValue | null) { const text = String(value ?? "").trim(); return text ? Number(text) : null; }
function optionalText(value: FormDataEntryValue | null) { const text = String(value ?? "").trim(); return text || null; }

function FlowSteps({ module, view }: { module: ModuleCode; view: FlowView }) {
  const { user } = useAuth();
  const items = module === "procurement"
    ? [
      { number: "1", title: "AI 初步选品", detail: "任务状态与选品表", href: "/procurement/selection", permission: "selection.read" as Permission, views: ["overview", "ai-selection"] as FlowView[] },
      { number: "2", title: "采购询价", detail: "人工登记询价表", href: "/procurement/quotes", permission: "quote.read" as Permission, views: ["quotation"] as FlowView[] },
      { number: "3", title: "利润复核", detail: "公式结果与 AI 解释", href: "/procurement/profit-reviews", permission: "profit_review.read" as Permission, views: ["profit"] as FlowView[] },
    ]
    : [
      { number: "1", title: "利润候选", detail: "查看复核后的候选", href: "/operations/profit-selections", permission: "profit_review.read" as Permission, views: ["overview", "profit"] as FlowView[] },
      { number: "2", title: "人工复选", detail: "人工选择或淘汰", href: "/operations/final-selection", permission: "final_selection.read" as Permission, views: ["final"] as FlowView[] },
      { number: "3", title: "竞品资料", detail: "3 条标题与五点", href: "/operations/competitors", permission: "final_selection.read" as Permission, views: ["competitors"] as FlowView[] },
      { number: "4", title: "Listing 文案", detail: "标题与五点草稿", href: "/operations/listings", permission: "listing_copy.read" as Permission, views: ["listing"] as FlowView[] },
    ];
  return <nav className="flow-step-grid" aria-label="业务流程">{items.filter((item) => can(user, item.permission)).map((item) => { const active = item.views.includes(view); return <Link className={active ? "active" : ""} href={item.href} key={item.href}><span>{item.number}</span><span><strong>{item.title}</strong><small>{item.detail}</small></span><em>{active ? "当前" : "查看"}</em><ChevronRight /></Link>; })}</nav>;
}

function SelectionTable({ records, stores, selectedId, onSelect }: { records: SelectionRecord[]; stores: Store[]; selectedId: string | null; onSelect: (id: string) => void }) {
  if (!records.length) return <div className="flow-empty"><TableProperties /><strong>当前店铺暂无选品记录</strong><span>这里只展示后端返回且属于账号授权范围的数据。</span></div>;
  const storeNames = new Map(stores.map((store) => [store.store_id, store.display_name]));
  return <div className="table-wrap"><table className="selection-table"><thead><tr><th>商品 / 记录</th><th>店铺</th><th>来源</th><th>业务阶段</th><th>来源快照</th><th>版本</th><th>负责人</th><th>更新时间</th><th>操作</th></tr></thead><tbody>{records.map((record) => <tr key={record.selection_id} className={selectedId === record.selection_id ? "selected" : ""}><td><button className="record-button" onClick={() => onSelect(record.selection_id)}><strong>{record.product_name}</strong><small>{record.marketplace} · {record.selection_id.slice(0, 8)}</small></button></td><td>{storeNames.get(record.store_id) ?? record.store_id}</td><td><span>{record.source_type}</span><small className="row-id">{record.source_version}</small></td><td><span className={`flow-status status-${record.stage}`}>{stageLabel[record.stage]}</span></td><td><span className={`source-state ${record.source_snapshot_ref ? "confirmed" : "missing"}`}>{record.source_snapshot_ref ? "已记录" : "缺失"}</span></td><td><strong>r{record.revision}</strong></td><td>{record.owner_id ?? "待分配"}</td><td>{formatTime(record.updated_at)}</td><td><button className="table-action" onClick={() => onSelect(record.selection_id)}>查看</button></td></tr>)}</tbody></table></div>;
}

function RecordOverview({ record, store }: { record: SelectionRecord | null; store?: Store }) {
  if (!record) return <div className="flow-empty"><TableProperties /><strong>请选择一条记录</strong><span>记录详情会显示来源、版本与当前阻断。</span></div>;
  const blockers = [!record.source_snapshot_ref ? "来源快照缺失" : null, !record.owner_id ? "负责人待分配" : null].filter(Boolean);
  return <div className="record-overview"><div className="record-overview-title"><span className="record-glyph"><TableProperties /></span><div><strong>{record.product_name}</strong><small>{record.selection_id}</small></div></div><dl><div><dt>授权店铺</dt><dd>{store?.display_name ?? record.store_id}</dd></div><div><dt>当前阶段</dt><dd><span className={`flow-status status-${record.stage}`}>{stageLabel[record.stage]}</span></dd></div><div><dt>来源与版本</dt><dd>{record.source_type} · {record.source_version}</dd></div><div><dt>当前修订</dt><dd>r{record.revision}</dd></div><div><dt>负责人</dt><dd>{record.owner_id ?? "待分配"}</dd></div><div><dt>最后更新</dt><dd>{formatTime(record.updated_at)}</dd></div></dl><section className={blockers.length ? "record-blockers has-blocker" : "record-blockers"}><AlertTriangle /><div><strong>当前阻断</strong><p>{blockers.length ? blockers.join("、") : "没有从当前契约识别到阻断项。"}</p></div></section><section className="version-note"><CircleHelp /><div><strong>版本记录</strong><p>当前接口返回修订号与来源版本；历史版本列表等待后端契约提供。</p></div></section></div>;
}

function NotAvailable({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="flow-unavailable"><Info /><div><strong>{title}</strong><p>{children}</p></div></div>;
}

function AiTasks({ tasks = [], type }: { tasks?: AiTask[]; type?: AiTask["task_type"] }) {
  const filtered = type ? tasks.filter((task) => task.task_type === type) : tasks;
  if (!filtered.length) return <NotAvailable title="AI 能力未配置 / 暂不可用">后端尚未返回该类型任务；页面不会模拟生成成功。</NotAvailable>;
  return <div className="ai-task-list">{filtered.map((task) => <article key={task.task_id}><div><Bot /><span><strong>{taskLabel[task.task_type]}</strong><small>{task.task_id} · 输入 {task.input_version}</small></span></div><span className={`task-state task-${task.status}`}>{taskStatusLabel[task.status]}</span><dl><div><dt>run_id</dt><dd>{task.run_id ?? "不可用"}</dd></div><div><dt>结果版本</dt><dd>{task.result_version ?? "不可用"}</dd></div><div><dt>错误代码</dt><dd>{task.error_code ?? "—"}</dd></div></dl></article>)}</div>;
}

function QuotationForm({ record, quotation, editable, onSave }: { record: SelectionRecord; quotation: Quotation | null | undefined; editable: boolean; onSave: (input: QuotationInput) => Promise<void> }) {
  const [saving, setSaving] = useState(false);
  return <form className="flow-form" onSubmit={async (event) => { event.preventDefault(); setSaving(true); const data = new FormData(event.currentTarget); try { await onSave({ supplier_name: String(data.get("supplier_name") ?? "").trim(), unit_cost: optionalText(data.get("unit_cost")), currency: String(data.get("currency") ?? "USD").toUpperCase(), value_status: String(data.get("value_status")) as ValueStatus, moq: optionalNumber(data.get("moq")), lead_time_days: optionalNumber(data.get("lead_time_days")), freight_per_unit: optionalText(data.get("freight_per_unit")), other_cost_per_unit: optionalText(data.get("other_cost_per_unit")), target_price: optionalText(data.get("target_price")), notes: optionalText(data.get("notes")), expected_revision: record.revision }); } finally { setSaving(false); } }}>
    <div className="flow-form-grid"><label>供应商<input name="supplier_name" required disabled={!editable} defaultValue={quotation?.supplier_name ?? ""} /></label><label>币种<input name="currency" required minLength={3} maxLength={3} disabled={!editable} defaultValue={quotation?.currency ?? "USD"} /></label><label>单件成本<input name="unit_cost" type="number" min="0" step="0.0001" disabled={!editable} defaultValue={quotation?.unit_cost ?? ""} /></label><label>数据状态<select name="value_status" disabled={!editable} defaultValue={quotation?.value_status ?? "missing"}>{Object.entries(valueLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>MOQ<input name="moq" type="number" min="1" disabled={!editable} defaultValue={quotation?.moq ?? ""} /></label><label>交期（天）<input name="lead_time_days" type="number" min="0" disabled={!editable} defaultValue={quotation?.lead_time_days ?? ""} /></label><label>单件运费<input name="freight_per_unit" type="number" min="0" step="0.0001" disabled={!editable} defaultValue={quotation?.freight_per_unit ?? ""} /></label><label>其他单件成本<input name="other_cost_per_unit" type="number" min="0" step="0.0001" disabled={!editable} defaultValue={quotation?.other_cost_per_unit ?? ""} /></label><label>目标售价<input name="target_price" type="number" min="0" step="0.0001" disabled={!editable} defaultValue={quotation?.target_price ?? ""} /></label></div>
    <label>询价备注<textarea name="notes" rows={3} disabled={!editable} defaultValue={quotation?.notes ?? ""} /></label>
    <div className="flow-form-footer"><span>{quotation ? `询价版本 v${quotation.version} · ${formatTime(quotation.created_at)}` : "尚未登记询价"}</span>{editable ? <button className="primary-button" disabled={saving}><Save />{saving ? "保存中…" : "保存询价"}</button> : <small>当前账号仅可查看</small>}</div>
  </form>;
}

function ProfitPanel({ profit }: { profit: ProfitReview | null | undefined }) {
  if (!profit) return <NotAvailable title="利润复核暂不可用">尚无利润复核版本，或 DeepSeek / 相关运行尚未配置。</NotAvailable>;
  return <div className="profit-panel"><div className="profit-summary"><span><small>利润额</small><strong>{profit.margin_amount ?? valueLabel[profit.value_status]}</strong></span><span><small>利润率</small><strong>{profit.margin_rate === null ? valueLabel[profit.value_status] : `${profit.margin_rate}%`}</strong></span><span><small>币种</small><strong>{profit.currency ?? "不可用"}</strong></span><span><small>数据状态</small><strong className={`value-${profit.value_status}`}>{valueLabel[profit.value_status]}</strong></span></div><section><h3>复核建议</h3><p>{profit.recommendation}</p><h3>复核依据</h3><p>{profit.explanation ?? "解释缺失"}</p></section>{profit.missing_inputs.length ? <div className="missing-data"><AlertTriangle /><div><strong>缺失数据</strong><p>{profit.missing_inputs.join("、")}</p></div></div> : null}<footer>利润版本 v{profit.version} · 基于询价 v{profit.quotation_version} · task {profit.task_id} · run {profit.run_id ?? "不可用"}</footer></div>;
}

function FinalForm({ record, final, editable, onSave }: { record: SelectionRecord; final: FinalSelection | null | undefined; editable: boolean; onSave: (input: { decision: "selected" | "rejected"; reason: string | null; expected_revision: number }) => Promise<void> }) {
  const [saving, setSaving] = useState(false);
  return <form className="flow-form" onSubmit={async (event) => { event.preventDefault(); setSaving(true); const data = new FormData(event.currentTarget); try { await onSave({ decision: String(data.get("decision")) as "selected" | "rejected", reason: optionalText(data.get("reason")), expected_revision: record.revision }); } finally { setSaving(false); } }}><div className="decision-options"><label><input type="radio" name="decision" value="selected" required disabled={!editable} defaultChecked={final?.decision === "selected"} />选择进入最终选品表</label><label><input type="radio" name="decision" value="rejected" required disabled={!editable} defaultChecked={final?.decision === "rejected"} />淘汰候选</label></div><label>人工复选理由<textarea name="reason" rows={4} maxLength={2000} disabled={!editable} defaultValue={final?.reason ?? ""} /></label><div className="flow-form-footer"><span>{final ? `最终选品版本 v${final.version} · 基于利润复核 v${final.profit_review_version}` : "尚未形成最终选品版本"}</span>{editable ? <button className="primary-button" disabled={saving}><Save />{saving ? "保存中…" : "保存人工决定"}</button> : <small>当前账号仅可查看</small>}</div></form>;
}

function CompetitorForm({ record, data, editable, onSave }: { record: SelectionRecord; data: CompetitorList | null | undefined; editable: boolean; onSave: (input: { competitors: CompetitorInput[]; expected_revision: number }) => Promise<void> }) {
  const defaults = Array.from({ length: 3 }, (_, index) => data?.competitors[index] ?? { title: "", bullets: ["", "", "", "", ""] });
  const [saving, setSaving] = useState(false);
  return <form className="competitor-form" onSubmit={async (event) => { event.preventDefault(); setSaving(true); const form = new FormData(event.currentTarget); const competitors = defaults.map((_, index) => ({ title: String(form.get(`title-${index}`) ?? "").trim(), bullets: Array.from({ length: 5 }, (__, bullet) => String(form.get(`bullet-${index}-${bullet}`) ?? "").trim()) })); try { await onSave({ competitors, expected_revision: record.revision }); } finally { setSaving(false); } }}>{defaults.map((competitor, index) => <fieldset key={index} disabled={!editable}><legend>竞品 {index + 1}</legend><label>标题<input name={`title-${index}`} required maxLength={1000} defaultValue={competitor.title} /></label><div className="bullet-inputs">{competitor.bullets.map((bullet, bulletIndex) => <label key={bulletIndex}><span>{bulletIndex + 1}</span><input name={`bullet-${index}-${bulletIndex}`} required maxLength={1000} defaultValue={bullet} placeholder={`五点要点 ${bulletIndex + 1}`} /></label>)}</div></fieldset>)}<div className="flow-form-footer"><span>{data ? `关联最终选品 v${data.final_version} · 当前记录 r${data.revision}` : "尚未登记竞品资料"}</span>{editable ? <button className="primary-button" disabled={saving}><Save />{saving ? "保存中…" : "保存 3 条竞品"}</button> : <small>当前账号仅可查看</small>}</div></form>;
}

function ListingPanel({ listing, final, competitors, tasks }: { listing?: ListingDraft | null; final?: FinalSelection | null; competitors?: CompetitorList | null; tasks?: AiTask[] }) {
  if (!final || final.decision !== "selected") return <NotAvailable title="Listing 文案暂不可用">需要先形成“已选中”的最终选品版本。</NotAvailable>;
  if (!competitors || competitors.competitors.length !== 3) return <NotAvailable title="竞品资料未完成">需要先保存 3 条竞品标题及各自 5 条要点。</NotAvailable>;
  if (!listing) return <><NotAvailable title="DeepSeek Listing 能力未配置 / 暂不可用">后端尚未生成草稿；当前契约没有启动接口，页面不会模拟成功。</NotAvailable><AiTasks tasks={tasks} type="listing_draft" /></>;
  return <article className="listing-draft"><header><div><small>运营文案版本</small><strong>v{listing.version}</strong></div><span>{listing.status}</span></header><h3>{listing.title}</h3><ol>{listing.bullets.map((bullet, index) => <li key={index}>{bullet}</li>)}</ol><footer>关联最终选品 v{listing.final_version} · task {listing.task_id} · run {listing.run_id ?? "不可用"} · {formatTime(listing.created_at)}</footer></article>;
}

export function SelectionWorkbench({ module, pathname }: { module: "operations" | "procurement"; pathname: string }) {
  const { user, stores, selectedStoreId } = useAuth();
  const view = viewByPath[pathname] ?? "overview";
  const [records, setRecords] = useState<SelectionRecord[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mutation, setMutation] = useState<{ kind: "success" | "conflict" | "error"; text: string } | null>(null);
  const [detailNonce, setDetailNonce] = useState(0);
  const [query, setQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<SelectionRecord["stage"] | "all">("all");
  const deferredQuery = useDeferredValue(query.trim().toLocaleLowerCase("zh-CN"));
  const visibleRecords = useMemo(() => records?.filter((record) => {
    if (selectedStoreId && record.store_id !== selectedStoreId) return false;
    if (stageFilter !== "all" && record.stage !== stageFilter) return false;
    if (!deferredQuery) return true;
    return `${record.product_name} ${record.selection_id} ${record.source_type}`.toLocaleLowerCase("zh-CN").includes(deferredQuery);
  }) ?? [], [records, selectedStoreId, stageFilter, deferredQuery]);
  const selected = visibleRecords.find((record) => record.selection_id === selectedId) ?? visibleRecords[0] ?? null;
  const detailSelectionId = selected?.selection_id ?? null;
  const store = stores.find((item) => item.store_id === selectedStoreId);

  const loadRecords = useCallback(async () => {
    setError(null);
    try { const response = await repository.list(); setRecords(response.items); setSelectedId((current) => response.items.some((item) => item.selection_id === current) ? current : response.items[0]?.selection_id ?? null); }
    catch (cause) { setRecords([]); setError(cause instanceof ApiError && cause.status === 403 ? "后端拒绝访问选品记录。" : "选品记录加载失败，请检查后端服务。" ); }
  }, []);

  useEffect(() => { const timer = window.setTimeout(() => { void loadRecords(); }, 0); return () => window.clearTimeout(timer); }, [loadRecords]);
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(async () => {
      setDetail(null); setError(null);
      if (!detailSelectionId || view === "overview") return;
      try {
        let next: Detail = {};
        if (view === "ai-selection") next = { tasks: (await repository.aiTasks(detailSelectionId)).items };
        if (view === "quotation") next = { quotation: await repository.quotation(detailSelectionId) };
        if (view === "profit") { const [profit, tasks] = await Promise.all([repository.profitReview(detailSelectionId), repository.aiTasks(detailSelectionId)]); next = { profit, tasks: tasks.items }; }
        if (view === "final") { const [profit, final] = await Promise.all([repository.profitReview(detailSelectionId), repository.finalSelection(detailSelectionId)]); next = { profit, final }; }
        if (view === "competitors") { const [final, competitors] = await Promise.all([repository.finalSelection(detailSelectionId), repository.competitors(detailSelectionId)]); next = { final, competitors }; }
        if (view === "listing") { const [final, competitors, listing, tasks] = await Promise.all([repository.finalSelection(detailSelectionId), repository.competitors(detailSelectionId), repository.listingDraft(detailSelectionId), repository.aiTasks(detailSelectionId)]); next = { final, competitors, listing, tasks: tasks.items }; }
        if (active) setDetail(next);
      } catch (cause) { if (active) setError(cause instanceof ApiError && cause.status === 403 ? "当前账号没有读取此成果的权限。" : "关联成果加载失败，请稍后重试。" ); }
    }, 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [detailSelectionId, view, detailNonce]);

  async function mutate(request: Promise<unknown>) {
    setMutation(null);
    try { await request; setMutation({ kind: "success", text: "已保存到后端，新版本将在刷新后继续使用。" }); await loadRecords(); setDetailNonce((value) => value + 1); }
    catch (cause) { if (cause instanceof ApiError && cause.status === 409) setMutation({ kind: "conflict", text: "版本冲突：记录已被其他人修改，请刷新后再提交。" }); else setMutation({ kind: "error", text: cause instanceof ApiError && cause.status === 403 ? "后端拒绝本次修改。" : "保存失败，请检查填写内容或后端状态。" }); }
  }

  function detailContent() {
    if (!selected) return <div className="flow-empty"><TableProperties /><strong>请选择一条记录</strong></div>;
    if (error) return <NotAvailable title="无法读取当前成果">{error}</NotAvailable>;
    if (!detail) return <div className="flow-loading"><span className="spinner" /><strong>正在加载关联记录与版本</strong></div>;
    if (view === "ai-selection") return <AiTasks tasks={detail.tasks} type="initial_selection" />;
    if (view === "quotation") return <QuotationForm key={`${selected.selection_id}-${detail.quotation?.version ?? 0}`} record={selected} quotation={detail.quotation} editable={can(user, "quote.manage")} onSave={(input) => mutate(repository.saveQuotation(selected.selection_id, input))} />;
    if (view === "profit") return <><ProfitPanel profit={detail.profit} /><div className="section-gap"><AiTasks tasks={detail.tasks} type="profit_review" /></div></>;
    if (view === "final") return <><ProfitPanel profit={detail.profit} /><div className="section-gap"><FinalForm key={`${selected.selection_id}-${detail.final?.version ?? 0}`} record={selected} final={detail.final} editable={can(user, "final_selection.manage")} onSave={(input) => mutate(repository.saveFinalSelection(selected.selection_id, input))} /></div></>;
    if (view === "competitors") return detail.final?.decision === "selected" ? <CompetitorForm key={`${selected.selection_id}-${detail.competitors?.revision ?? 0}`} record={selected} data={detail.competitors} editable={can(user, "competitor_reference.manage")} onSave={(input) => mutate(repository.saveCompetitors(selected.selection_id, input))} /> : <NotAvailable title="竞品资料暂不可编辑">只有人工复选为“已选中”的记录才能维护竞品资料。</NotAvailable>;
    return <ListingPanel listing={detail.listing} final={detail.final} competitors={detail.competitors} tasks={detail.tasks} />;
  }

  const copy = viewCopy[view];
  const pageTitle = module === "procurement" && view === "overview" ? "采购工具台" : module === "operations" && view === "overview" ? "运营工作台" : module === "operations" && view === "profit" ? "利润选品表" : copy.title;
  const selectedStore = stores.find((item) => item.store_id === selected?.store_id);
  return <div className="selection-workbench"><div className="page-heading"><div><h1>{pageTitle}</h1><p>{copy.description}</p></div><span className="scope-label">{store ? `${store.display_name} · ${store.marketplace}` : "后端授权店铺范围"}</span></div><div className="source-notice api"><CheckCircle2 /><strong>真实后端记录</strong><span>所有表格通过 selection_id 与版本关联。</span><i /><Info /><span>AI 未接入时明确显示未配置或暂不可用。</span></div><FlowSteps module={module} view={view} />{mutation ? <div className={`mutation-message mutation-${mutation.kind}`} role="status">{mutation.kind === "conflict" ? <AlertTriangle /> : mutation.kind === "success" ? <CheckCircle2 /> : <Info />}<span>{mutation.text}</span>{mutation.kind === "conflict" ? <button onClick={() => { void loadRecords(); setDetailNonce((value) => value + 1); }}><RefreshCw />刷新记录</button> : null}</div> : null}<section className="selection-layout"><div className="panel selection-list-panel"><div className="panel-heading"><div><h2>{module === "procurement" ? "选品表" : "利润候选记录"}</h2><p>{records === null ? "正在加载…" : `${visibleRecords.length} 条 · 仅当前授权店铺`}</p></div><button className="secondary-button" onClick={() => void loadRecords()}><RefreshCw />刷新</button></div><div className="selection-toolbar"><label className="selection-search"><Search /><span className="sr-only">搜索商品或记录编号</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索商品或记录编号" /></label><label className="selection-filter"><ListFilter /><span className="sr-only">业务阶段筛选</span><select value={stageFilter} onChange={(event) => setStageFilter(event.target.value as SelectionRecord["stage"] | "all")}><option value="all">全部阶段</option>{Object.entries(stageLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{module === "procurement" && can(user, "selection.create") ? <button className="primary-button ai-create-button" disabled title="AI 选品任务启动接口尚未配置"><Sparkles />新建 AI 选品任务</button> : null}</div>{error && view === "overview" ? <NotAvailable title="列表加载失败">{error}</NotAvailable> : records === null ? <div className="flow-loading"><span className="spinner" /><strong>正在加载选品表</strong></div> : <SelectionTable records={visibleRecords} stores={stores} selectedId={selected?.selection_id ?? null} onSelect={setSelectedId} />}<div className="table-state-legend"><span>状态说明</span><i className="confirmed">已记录</i><i className="missing">缺失</i><i className="unavailable">暂不可用</i><i className="failed">任务失败</i></div></div><div className="panel selection-detail-panel"><div className="panel-heading"><div><h2>{view === "overview" ? "记录详情" : `${pageTitle}详情`}</h2><p>{selected ? `${selected.product_name} · r${selected.revision}` : "未选择记录"}</p></div>{selected ? <span className="record-version">来源 {selected.source_version}</span> : null}</div><div className="selection-detail-body">{view === "overview" ? <RecordOverview record={selected} store={selectedStore} /> : detailContent()}</div>{view === "overview" ? <div className="flow-boundary"><FilePenLine /><div><strong>当前阶段边界</strong><p>{module === "procurement" ? "采购执行页面归属尚未确认，本轮不提供下单或批准入口。" : "运营负责人工复选和竞品资料；Listing 草稿是否可编辑由后端权限决定。"}</p></div></div> : null}</div></section></div>;
}
