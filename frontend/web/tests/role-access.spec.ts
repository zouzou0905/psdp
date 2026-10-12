import { expect, test, type Page, type Route } from "@playwright/test";

type Account = "operations_demo" | "procurement_demo" | "creative_demo" | "admin_demo";
interface BackendState { account: Account | null; available: boolean; logoutUnauthorized: boolean; conflictNext: boolean; revision: number; quotation: Record<string, unknown> | null }
const backendStates = new WeakMap<Page, BackendState>();
const permissions = {
  operations_demo: ["operations.dashboard.read", "selection.read", "profit_review.read", "final_selection.read", "final_selection.manage", "competitor_reference.manage", "listing_copy.read"],
  procurement_demo: ["procurement.dashboard.read", "selection.read", "profit_review.read", "final_selection.read", "quote.read", "quote.manage"],
  creative_demo: ["creative.dashboard.read", "generation.request", "asset.read", "review_comment.read"],
  admin_demo: ["admin.dashboard.read", "user.manage", "role.manage", "task.read_all", "error.read", "ai_feedback.read_all", "audit_log.read", "capability.read", "system_health.read", "all_business.read", "operations.dashboard.read", "selection.read", "profit_review.read", "final_selection.read", "final_selection.manage", "competitor_reference.manage", "procurement.dashboard.read", "quote.read", "quote.manage", "creative.dashboard.read"],
} as const;
const modules = { operations_demo: ["operations"], procurement_demo: ["procurement"], creative_demo: ["creative"], admin_demo: ["operations", "procurement", "creative", "admin"] } as const;

function context(account: Account) {
  const moduleCode = account.replace("_demo", "");
  return { user: { user_id: `00000000-0000-4000-8000-${account.padEnd(12, "0").slice(0, 12)}`, username: account, display_name: `${moduleCode} 测试账号` }, roles: [moduleCode], modules: modules[account], permissions: permissions[account], scopes: { organization_ids: ["org_demo"], team_ids: ["team_demo"], store_ids: account === "creative_demo" ? [] : ["store_us_a", "store_ca_b"] }, default_landing: `/${moduleCode}`, authorization_revision: 1 };
}

function dashboard(module: string) {
  const records = module === "operations" ? { work_items: [], projects: [] } : module === "procurement" ? { purchase_requests: [] } : module === "creative" ? { content_tasks: [] } : { readable_modules: ["operations", "procurement", "creative", "admin"] };
  const counts = module === "operations" ? { pending_tasks: 0, active_projects: 0, exceptions: 0 } : module === "procurement" ? { pending_requests: 0, open_quotes: 0, fulfillment_exceptions: 0 } : module === "creative" ? { pending_content_tasks: 0, assets_in_review: 0, generation_failures: 0 } : { open_errors: 0, pending_ai_feedback: 0, audit_events: 0 };
  return { viewer: { user_id: "viewer", display_name: "测试账号", role: module }, generated_at: "2026-10-07T08:00:00Z", data_status: "confirmed", disclaimer: "测试契约数据", workspace: module, counts, alerts: [], ...records };
}

async function mockBackend(page: Page) {
  const existing = backendStates.get(page);
  if (existing) return existing;
  const state: BackendState = { account: null, available: true, logoutUnauthorized: false, conflictNext: false, revision: 1, quotation: null };
  backendStates.set(page, state);
  await page.route("http://localhost:8000/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (!state.available) return route.abort("connectionrefused");
    if (path === "/api/v1/auth/login") {
      const body = request.postDataJSON() as { username: Account; password: string };
      if (!(body.username in modules) || body.password !== "test-password") return route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "invalid credentials" }) });
      state.account = body.username;
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(context(body.username)) });
    }
    if (path === "/api/v1/auth/logout") {
      if (!state.account || state.logoutUnauthorized) return route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "not authenticated" }) });
      state.account = null;
      return route.fulfill({ status: 204 });
    }
    if (!state.account) return route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "not authenticated" }) });
    if (path === "/api/v1/me/access-context") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(context(state.account)) });
    if (path === "/api/v1/me/stores") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: state.account !== "creative_demo" ? [
      { store_id: "store_us_a", display_name: "美国一店", marketplace: "Amazon US", organization_id: "org_demo", status: "active", credential_configured: true, revision: 1, created_at: "2026-10-01T00:00:00Z", updated_at: "2026-10-01T00:00:00Z" },
      { store_id: "store_ca_b", display_name: "加拿大二店", marketplace: "Amazon CA", organization_id: "org_demo", status: "active", credential_configured: true, revision: 1, created_at: "2026-10-01T00:00:00Z", updated_at: "2026-10-01T00:00:00Z" },
    ] : [], total: state.account !== "creative_demo" ? 2 : 0 }) });
    const selections = [
      { selection_id: "60000000-0000-4000-8000-000000000001", store_id: "store_us_a", marketplace: "amazon-us", product_name: "折叠收纳架", source_type: "ai_skill_sorftime", source_ref: "task://initial-1", source_snapshot_ref: "snapshot://market-1", source_version: "skill-v1", owner_id: null, stage: state.quotation ? "quoted" : "sourced", revision: state.revision, created_at: "2026-10-08T00:00:00Z", updated_at: "2026-10-08T01:00:00Z" },
      { selection_id: "60000000-0000-4000-8000-000000000002", store_id: "store_ca_b", marketplace: "amazon-ca", product_name: "桌面理线盒", source_type: "ai_skill_sorftime", source_ref: "task://initial-2", source_snapshot_ref: "snapshot://market-2", source_version: "skill-v1", owner_id: null, stage: "profit_reviewed", revision: 3, created_at: "2026-10-08T00:00:00Z", updated_at: "2026-10-08T02:00:00Z" },
    ];
    if (path === "/api/v1/selection-records") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: selections, total: selections.length }) });
    const selectionMatch = path.match(/^\/api\/v1\/selection-records\/([^/]+)(?:\/(quotation|profit-review|final-selection|competitors|ai-tasks|listing-draft))?$/);
    if (selectionMatch) {
      const [, id, child] = selectionMatch;
      const record = selections.find((item) => item.selection_id === id);
      if (!record) return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "not found" }) });
      if (child === "quotation" && request.method() === "PUT") { if (state.conflictNext) { state.conflictNext = false; return route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: "Selection changed; reload before updating" }) }); } const body = request.postDataJSON() as Record<string, unknown>; state.revision += 1; state.quotation = { quotation_id: "70000000-0000-4000-8000-000000000001", selection_id: id, version: 1, supplier_name: body.supplier_name, unit_cost: body.unit_cost, currency: body.currency, value_status: body.value_status, moq: body.moq, lead_time_days: body.lead_time_days, freight_per_unit: body.freight_per_unit, other_cost_per_unit: body.other_cost_per_unit, target_price: body.target_price, notes: body.notes, recorded_by: "user", created_at: "2026-10-08T03:00:00Z" }; return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(state.quotation) }); }
      if (child === "quotation") return state.quotation ? route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(state.quotation) }) : route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "not available" }) });
      if (child === "profit-review") return id.endsWith("2") ? route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ profit_review_id: "80000000-0000-4000-8000-000000000001", selection_id: id, version: 1, quotation_version: 1, margin_amount: null, margin_rate: null, currency: "USD", value_status: "missing", recommendation: "资料不足，暂不形成盈利结论", explanation: "缺少平台费用。", missing_inputs: ["marketplace_fee"], task_id: "profit-1", run_id: null, created_at: "2026-10-08T03:00:00Z" }) }) : route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "not available" }) });
      if (child === "ai-tasks") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: [{ task_id: `task-${id.slice(-1)}`, selection_id: id, task_type: "initial_selection", input_version: "skill-v1", status: "planned", run_id: null, result_version: null, error_code: null, created_at: "2026-10-08T00:00:00Z", updated_at: "2026-10-08T00:00:00Z" }], total: 1 }) });
      if (child === "final-selection" && state.account === "operations_demo" && id.endsWith("1")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ final_selection_id: "90000000-0000-4000-8000-000000000001", selection_id: id, version: 1, profit_review_version: 1, decision: "selected", reason: "运营人工复选通过", decided_by: "operations-user", created_at: "2026-10-08T04:00:00Z" }) });
      if (child === "competitors" && state.account === "operations_demo" && id.endsWith("1")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ selection_id: id, final_version: 1, revision: 4, competitors: Array.from({ length: 3 }, (_, index) => ({ competitor_id: `competitor-${index + 1}`, position: index + 1, title: `竞品 ${index + 1}`, bullets: Array.from({ length: 5 }, (__, bullet) => `要点 ${bullet + 1}`) })) }) });
      if (child === "listing-draft") {
        if (state.account !== "operations_demo") return route.fulfill({ status: 403, contentType: "application/json", body: JSON.stringify({ detail: "forbidden" }) });
        if (id.endsWith("1")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ listing_draft_id: "a0000000-0000-4000-8000-000000000001", selection_id: id, version: 2, final_version: 1, title: "运营专属 Listing 草稿", bullets: ["卖点一", "卖点二", "卖点三", "卖点四", "卖点五"], status: "draft", task_id: "listing-task-1", run_id: "listing-run-1", created_at: "2026-10-08T05:00:00Z" }) });
      }
      if (["final-selection", "competitors", "listing-draft"].includes(child ?? "")) return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "not available" }) });
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(record) });
    }
    const match = path.match(/^\/api\/v1\/(operations|procurement|creative|admin)\/dashboard$/);
    if (match) {
      const requested = match[1];
      if (!modules[state.account].includes(requested as never)) return route.fulfill({ status: 403, contentType: "application/json", body: JSON.stringify({ detail: "forbidden" }) });
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(dashboard(requested)) });
    }
    if (path === "/api/v1/admin/errors") return route.fulfill({ status: state.account === "admin_demo" ? 200 : 403, contentType: "application/json", body: JSON.stringify({ items: [], total: 0 }) });
    return route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
  });
  return state;
}

async function loginAs(page: Page, account: Account) {
  await page.goto("/login");
  await page.getByLabel("账号").fill(account);
  await page.getByLabel("密码").fill("test-password");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/${account.replace("_demo", "")}$`));
}

test.beforeEach(async ({ page }) => { await mockBackend(page); });

test("登录页只显示账号密码，不显示四角色入口", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByLabel("账号")).toBeVisible();
  await expect(page.getByLabel("密码")).toBeVisible();
  await expect(page.getByText("演示账号入口")).toHaveCount(0);
  await expect(page.getByTestId(/demo-login/)).toHaveCount(0);
  await page.screenshot({ path: "artifacts/auth-login.png", fullPage: true });
});

for (const [account, landing, heading] of [
  ["operations_demo", "/operations", "运营工作台"], ["procurement_demo", "/procurement", "采购工具台"],
  ["creative_demo", "/creative", "美工总览"], ["admin_demo", "/admin", "全局业务总览"],
] as const) test(`${account} 自动进入对应首页`, async ({ page }) => { await loginAs(page, account); await expect(page).toHaveURL(new RegExp(`${landing}$`)); await expect(page.getByRole("heading", { name: heading })).toBeVisible(); });

test("运营导航隔离、越权 URL 403、店铺仅来自后端范围", async ({ page }) => {
  await loginAs(page, "operations_demo");
  await expect(page.getByRole("link", { name: "利润选品表" })).toBeVisible();
  await expect(page.getByRole("link", { name: "用户管理" })).toHaveCount(0);
  await expect(page.getByLabel("授权店铺").locator("option")).toHaveCount(2);
  await expect(page.getByLabel("授权店铺")).toContainText("美国一店");
  await page.goto("/admin/errors");
  await expect(page.getByRole("heading", { name: "没有访问权限" })).toBeVisible();
});

test("采购账号没有 Listing 入口，直接访问旧路由显示 403", async ({ page }) => {
  await loginAs(page, "procurement_demo");
  await expect(page.getByRole("link", { name: "Listing 文案" })).toHaveCount(0);
  await expect(page.getByText("Listing 文案", { exact: true })).toHaveCount(0);
  await page.goto("/procurement/listings");
  await expect(page.getByRole("heading", { name: "没有访问权限" })).toBeVisible();
  await expect(page.getByText("运营专属 Listing 草稿")).toHaveCount(0);
});

test("运营账号按显式 Listing 权限显示入口", async ({ page }) => {
  await loginAs(page, "operations_demo");
  await expect(page.getByRole("link", { name: "Listing 文案" }).first()).toBeVisible();
  await page.goto("/operations/listings");
  await expect(page.getByRole("heading", { name: "Listing 文案", exact: true })).toBeVisible();
  await expect(page.getByText("运营专属 Listing 草稿")).toBeVisible();
});

test("没有 Listing 权限的管理员不显示业务入口", async ({ page }) => {
  await loginAs(page, "admin_demo");
  await expect(page.getByRole("link", { name: "Listing 文案" })).toHaveCount(0);
  await page.goto("/operations/listings");
  await expect(page.getByRole("heading", { name: "没有访问权限" })).toBeVisible();
});

test("退出并切换为采购账号后不残留 Listing 数据", async ({ page }) => {
  await loginAs(page, "operations_demo");
  await page.goto("/operations/listings");
  await expect(page.getByText("运营专属 Listing 草稿")).toBeVisible();
  await page.getByRole("button", { name: "退出" }).click();
  await loginAs(page, "procurement_demo");
  await expect(page.getByText("运营专属 Listing 草稿")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Listing 文案" })).toHaveCount(0);
});

test("授权店铺切换只显示对应选品记录", async ({ page }) => {
  await loginAs(page, "operations_demo");
  await expect(page.getByRole("button", { name: /折叠收纳架/ })).toBeVisible();
  await page.getByLabel("授权店铺").selectOption("store_ca_b");
  await expect(page.getByRole("button", { name: /桌面理线盒/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /折叠收纳架/ })).toHaveCount(0);
});

test("采购询价保存到后端并在刷新后恢复", async ({ page }) => {
  await loginAs(page, "procurement_demo");
  await page.goto("/procurement/quotes");
  await expect(page.getByRole("heading", { name: "采购询价", exact: true })).toBeVisible();
  await page.getByLabel("供应商").fill("测试供应商");
  await page.getByLabel("单件成本", { exact: true }).fill("8.25");
  await page.getByLabel("数据状态").selectOption("confirmed");
  await page.getByRole("button", { name: "保存询价" }).click();
  await expect(page.getByRole("status")).toContainText("已保存到后端");
  await page.reload();
  await expect(page.getByLabel("供应商")).toHaveValue("测试供应商");
  await expect(page.getByLabel("单件成本", { exact: true })).toHaveValue("8.25");
});

test("询价版本冲突时保留表单并提示刷新", async ({ page }) => {
  const state = await mockBackend(page);
  await loginAs(page, "procurement_demo");
  await page.goto("/procurement/quotes");
  await page.getByLabel("供应商").fill("冲突供应商");
  state.conflictNext = true;
  await page.getByRole("button", { name: "保存询价" }).click();
  await expect(page.getByRole("status")).toContainText("版本冲突");
  await expect(page.getByLabel("供应商")).toHaveValue("冲突供应商");
});

test("刷新恢复会话，注销后不能访问业务页面", async ({ page }) => {
  await loginAs(page, "creative_demo");
  await page.reload();
  await expect(page.getByRole("heading", { name: "美工总览" })).toBeVisible();
  await page.getByRole("button", { name: "退出" }).click();
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await page.goto("/creative");
  await expect(page).toHaveURL(/\/login\?next=/);
});

test("会话已失效时注销仍返回登录页且不产生运行时错误", async ({ page }) => {
  const runtimeErrors: string[] = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  const state = await mockBackend(page);
  await loginAs(page, "creative_demo");
  state.logoutUnauthorized = true;
  await page.getByRole("button", { name: "退出" }).click();
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await expect(page.getByRole("button", { name: "登录", exact: true })).toBeVisible();
  expect(runtimeErrors).toEqual([]);
});

test("会话失效清理 UI 并返回登录页", async ({ page }) => {
  const state = await mockBackend(page);
  await loginAs(page, "procurement_demo");
  state.account = null;
  await page.reload();
  await expect(page).toHaveURL(/\/login\?next=/);
});

test("后端不可用时显示明确错误", async ({ page }) => {
  const state = await mockBackend(page);
  state.available = false;
  await page.goto("/login");
  await page.getByLabel("账号").fill("operations_demo");
  await page.getByLabel("密码").fill("test-password");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page.locator(".login-error")).toContainText("后端服务或数据库暂不可用");
});

test("移动端工作台无整体横向溢出", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loginAs(page, "operations_demo");
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  expect(await page.evaluate(() => document.body.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: "artifacts/auth-operations-mobile.png", fullPage: true });
});
