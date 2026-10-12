# AI Product Operations Platform

本仓库用于构建“AI 商品运营中台”。目录名称保持英文，方便后续写代码、查找文件、跨工具协作和长期维护。

重要原则：

- `docs/direction/` 存放系统长期方向，不和项目执行文档混在一起。
- `docs/project/` 存放项目计划、排期、会议、阶段交付等执行文档。
- 代码、数据库、接口、AI 能力、测试、部署分别放入对应英文目录。
- `tmp/` 只放临时文件，不作为正式资料或代码来源。

## Root Folders

```text
TF/
  frontend/         前端应用
  backend/          后端服务
  database/         数据库结构、迁移和种子数据
  ai/               AI 能力、Skill、提示词、评测和案例
  integrations/     ERP、广告、市场数据、平台、MCP 等外部系统接入
  shared/           前后端和服务间共享的类型、契约和工具
  infrastructure/   部署、Docker、监控、环境配置
  scripts/          本地脚本和自动化工具
  tests/            单元测试、集成测试、端到端测试
  docs/             文档区
  tmp/              临时文件
```

## Code Areas

### frontend

前端代码目录。

```text
frontend/
  web/              业务工作台，例如选品、商品、任务、上架、运营看板
  admin/            管理后台，例如用户、权限、审批、发布、审计
```

### backend

后端代码目录。

```text
backend/
  api/              API 入口
  domain/           核心业务对象和领域规则
  services/         应用服务和业务用例
  workers/          异步任务、外部执行、状态回查、队列消费
```

### database

数据库相关目录。

```text
database/
  schemas/          表结构草案、ER 图、数据字典
  migrations/       数据库迁移文件
  seeds/            初始化数据、样例数据
```

### ai

AI 能力相关目录。

```text
ai/
  skills/           选品 Skill、Listing、图片、广告等能力适配
  prompts/          版本化提示词
  evals/            评测集、评测脚本、质量报告
  cases/            反馈案例、错误样本、回归样本
```

### integrations

外部系统接入目录。

```text
integrations/
  erp/              ERP 商品、采购、库存、发运等数据接入
  advertising/      广告系统接入
  marketplace/      Amazon 等平台上架、状态回查、Listing 接入
  sorftime/         Sorftime 或其他市场数据接入
  mcp/              MCP 工具和连接契约
```

### shared

共享代码目录。

```text
shared/
  types/            共享类型定义
  contracts/        API、任务、事件、外部动作契约
  utils/            通用工具函数
```

### infrastructure

部署和运行环境目录。

```text
infrastructure/
  docker/           Docker、compose 等本地或服务部署配置
  deploy/           发布脚本、部署配置
  monitoring/       日志、监控、告警、健康检查
```

### tests

测试目录。

```text
tests/
  unit/             单元测试
  integration/      集成测试
  e2e/              端到端测试
  fixtures/         测试数据和夹具
```

## Documentation Areas

```text
docs/
  direction/        系统长期方向和建设原则
  project/          项目计划、排期、资源、阶段交付
  requirements/     需求、岗位流程、业务规则、异常流程
  architecture/     技术架构、模块设计、数据流、系统边界
  decisions/        会议纪要、关键决策、待确认问题
```

当前方向文档：

```text
docs/direction/AI商品运营中台_系统构建方向.md
```

## 本地一键启动

Windows 下可直接双击：

```text
scripts/start-dev.cmd
```

脚本会检查 8000/3001 端口，启动 FastAPI 后端与 Next.js 前端，等待健康检查通过后自动打开 `http://localhost:3001`。脚本窗口需要保持开启；关闭窗口或按 `Ctrl+C` 会停止本次启动的服务。运行日志位于 `tmp/dev-logs/`。

默认启用明确标注的本地 Demo 登录，不依赖数据库中的演示账号。如需测试后端正式认证流程，可在 PowerShell 中执行：

```powershell
.\scripts\start-dev.ps1 -UseBackendAuth
```

该模式需要 PostgreSQL、数据库迁移及演示用户已按 `backend/api/README.md` 完成配置。

后续新对话或新任务开始前，优先读取这个方向文档，再进入具体代码或项目文档。

## Build Direction

2026-10-08 已确认当前阶段部分重构，优先路线为：

```text
DeepSeek + 用户 Skill + Sorftime MCP 选品
-> 选品表
-> 采购人工询价登记
-> DeepSeek 利润复核
-> 利润选品表
-> 运营人工复选并补充 3 条竞品标题和五点
-> 最终选品表
-> 采购人员采购

最终选品表 -> DeepSeek 按规定提示词生成本商品标题和五点草稿
```

采购工具台展示第 1、2、3 步，运营工作台展示第 4、6 步。Listing 文案为运营专属，普通采购账号无文案读取或操作权限；管理员也需显式文案权限。第 5 步页面位置仍待细化。完整执行指引见 `AGENTS.md` 和方向文档的“当前阶段重构方向”部分。

下列长期建设原则继续保留：

1. 以商品和经营项目为中心。
2. 以任务作为所有执行动作的载体。
3. 以审批、权限、版本、日志控制风险。
4. 以 AI Skill、提示词、案例库、评测和灰度发布支撑持续迭代。
5. 以 ERP、广告系统、平台上架工具和市场数据作为外部事实来源或执行边界。

任何代码模块都应尽量围绕这些边界放置，避免把业务逻辑散落在临时脚本、聊天记录或个人文件夹中。

当前后端统一 `.xlsx` 导出基座已注册 AI 选品表 `initial_selection` 和采购询价表 `quotation`。两者分别使用 `selection.export`、`quotation.export`，共享 PostgreSQL 冻结快照和受控下载；利润表及最终选品表尚未接入。
