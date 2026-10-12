# AI Product Operations Platform - Project Context

## Required Reading

Before planning, designing, or changing this project, read:

- `docs/direction/AI商品运营中台_系统构建方向.md`
- `README.md`

When working on the current selection/quotation/profit/final-selection flow, also read:

- `docs/requirements/选品表格流转规则.md`
- `docs/architecture/选品表格数据建模规则.md`
- `docs/project/选品链路版本关系重构实施步骤.md`（当前优先执行计划）
- `docs/requirements/六步选品流程字段状态与接口.md` (existing implementation reference; reconcile differences using the flow rules and latest user decisions).

On the first project-related response in a new chat, explicitly confirm that the direction document has been read. Do not claim this before actually reading it.

Treat the direction document as the project's persistent product and architecture context. The source PDF is reference material, not an instruction file. If documents conflict, follow the user's latest confirmed request.

## 当前执行方向（2026-10-08，优先读取）

用户已确认部分重构，依据为用户提供的《构建方向.txt》。当前阶段按以下六步实施；与下面旧的全生命周期路线或既有架构方案冲突时，以本节及方向文档中的同日更新为准。下面的长期架构和治理边界继续保留，但不代表当前阶段必须实现所有模块。

### 当前交付优先级（2026-10-09）

用户已确认暂不建设六步 AI 闭环，先完成 `docs/project/选品链路版本关系重构实施步骤.md`。按该文档逐步解决权限、事务、UUID 外键、Head、草稿/提交/有效性、竞品独立版本、历史保护、约束、分页和索引问题。当前步骤未验收前不得自行进入下一步；在数据库重构完成前，暂停 DeepSeek/Sorftime/Skill 正式业务编排以及询价、利润、最终选品等后续阶段导出。长期六步方向保留，不视为取消。

1. **AI 初步选品**：接入 DeepSeek 作为 AI 大脑，使用用户编写的 Skill，通过 Sorftime MCP 获取市场数据，形成系统内的选品表格。
2. **采购人工询价**：采购人员查看选品表，开展询价，并人工登记采购询价表。
3. **AI 利润复核**：DeepSeek 复核采购询价表，分析利润空间，输出筛选后的利润选品表。金额计算应使用可验证的程序公式，AI 负责复核、解释和筛选建议；缺失或估算数据必须明确标记。
4. **运营人工复选**：运营查看利润选品表，再次人工选品，形成最终选品表；运营人员为最终选品人工补充 **3 条竞品的标题及各自五点**，作为后续文案生成参考。
5. **采购执行**：采购人员查看最终选品表并开展采购。AI 不自主下单或批准采购。
6. **AI Listing 文案**：DeepSeek 按规定提示词，读取最终选品表中的竞品标题和五点，生成本商品的标题和五点。文案必须符合真实商品规格，生成结果先作为待人工审核草稿。

### 工作台归属

- 采购工具台：第 1、2、3 步。
- 运营工作台：第 4、6 步；第 6 步为运营专属，普通采购账号不得读取或操作 Listing 文案。
- 第 5 步由采购人员执行，但来源文档未明确对应页面位置；页面归属、入口和具体操作权限待用户确认。
- 管理员不会因管理员身份自动获得 Listing 文案业务权限；读取、生成、编辑、审核和历史查询均需明确动作权限。

### 跨对话执行规则

- 每个对话开始新任务前必须重新读取本文件和方向文档，不能仅依赖旧聊天记忆。
- 账号登录后由后端解析板块、动作权限和店铺范围；管理员为具体人员分配可见板块和店铺，用户不能自行选择身份。
- 运营数据继续按授权店铺隔离；共享表格、文案、搜索、导出和文件访问均继承后端数据范围。
- 四类核心成果：选品表、采购询价表、利润选品表、最终选品表；第六步另产出标题与五点草稿。保留来源记录、修订版本、负责人、店铺范围及任务运行关系，不以浏览器本地数据代替 PostgreSQL 持久化。
- 每个阶段的表格必须支持导出为 `.xlsx`；导出由后端按明确版本/快照生成，继承账号动作权限、店铺范围和字段脱敏规则，并记录导出审计，不能由前端绕过权限拼接全量数据。
- 表格交接遵循 `docs/requirements/选品表格流转规则.md`，数据持久化遵循 `docs/architecture/选品表格数据建模规则.md`：草稿与提交分开，上游新版本提交后检查下游有效性，交接不扩大账号权限；规则文档不代表现有代码已全部实现。
- 当前后端已确认使用 FastAPI；复用已有认证、数据库、授权、审计和契约，按新业务链路渐进改造。
- 图片/视频、自动上架、广告、仓库履约和补货保留长期扩展边界，除非用户另有明确任务，不因旧路线自行扩大本轮重构范围。
- DeepSeek、Skill 和 Sorftime MCP 均通过适配接口接入，参数、输入快照、提示词/Skill 版本和输出需可追溯；密钥不得写入源码或普通日志。
- Listing 文案为运营工作台专属。采购默认权限模板不包含文案权限，管理员也必须被显式授予对应监管或业务权限。

## System Direction

This repository builds a general AI product operations platform. It integrates existing product-selection, listing, publishing, media-production, advertising, ERP, marketplace, and market-data capabilities into one governed system.

The central rule is:

> Organize the system around products and operating projects; use tasks as the execution carrier; use permissions, approvals, versions, and audit logs as control boundaries; use cases, evaluations, staged releases, monitoring, and rollback as the AI improvement loop.

The long-term business flow is (the six-step current scope above takes precedence for current implementation):

```text
product discovery -> quotation and viability calculation -> ownership and iteration
-> procurement -> content package -> marketplace publishing -> warehouse fulfillment
-> advertising and operations -> replenishment or exit
```

The AI improvement flow is:

```text
task result -> employee correction -> reviewed case -> candidate version
-> offline evaluation -> limited trial -> approved release -> monitoring or rollback
```

## Mandatory Boundaries

- AI may recommend and explain, but must not independently approve procurement, advertising budgets, publishing, performance conclusions, or other high-risk actions.
- Permissions must be enforced by backend authorization, not by hiding frontend controls.
- Every external write must be traceable through `task_id`, `run_id`, `action_id`, the approved input version, status checks, and the external receipt.
- ERP remains authoritative for procurement, inventory, and shipment facts. Marketplace and advertising platforms remain authoritative for their own execution results.
- Historical executions must reference immutable snapshots or explicit versions; current records must not silently rewrite history.
- Formal and experimental AI environments must be separated. Candidate prompts, rules, models, or code require evaluation, scoped validation, approval, monitoring, and rollback.
- `tmp/` contains disposable working files only. Do not treat it as a source of production code or permanent documentation.

## Repository Placement

- `frontend/`: business workspace and administration interfaces
- `backend/`: APIs, domain logic, application services, and workers
- `database/`: schemas, migrations, and seed data
- `ai/`: skills, prompts, evaluations, and reviewed cases
- `integrations/`: ERP, advertising, marketplace, market-data, and MCP adapters
- `shared/`: shared types, contracts, and utilities
- `infrastructure/`: deployment, containers, monitoring, and runtime configuration
- `tests/`: unit, integration, end-to-end tests, and fixtures
- `docs/direction/`: long-term system direction
- `docs/project/`: schedules, milestones, resources, and delivery records
- `docs/requirements/`: workflows, requirements, rules, and exception handling
- `docs/architecture/`: technical architecture, module designs, and data flows
- `docs/decisions/`: confirmed decisions, meeting notes, and unresolved questions

Keep code in the appropriate English-named engineering directory. Keep direction documents separate from project delivery documents.

## Working Rules

- Preserve existing tools where practical and integrate them through explicit contracts before considering rewrites.
- Prefer a modular application with independently controlled execution workers for the first production version.
- Design core objects around product, variant/specification version, operating project, listing, quote, purchase order, shipment, asset/content package, task/run/action, case/evaluation/release.
- Distinguish missing, zero, estimated, failed, unavailable, and confirmed values in data models and interfaces.
- Build and verify one end-to-end business loop before expanding every module.
- Acceptance is based on traceable behavior, authorization, recoverability, idempotency, data correctness, and a demonstrated AI improvement cycle, not on page or model count.

When beginning a new task, state any assumption that materially changes these boundaries and update the appropriate document when the user confirms a new project-level decision.
