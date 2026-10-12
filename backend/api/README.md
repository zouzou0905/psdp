# Backend API

模块化 FastAPI 后端。当前包含 health、system、身份认证、后端授权、岗位工作区、管理员只读观测和岗位化 dashboard。演示数据始终标记为 `demo`，不代表正式经营事实。

## Requirements

- Python 3.12+
- 生产/本地联调：PostgreSQL 14+
- 可选：Redis/Celery（本阶段只保留配置和 Worker 边界，无需启动）

## Install

在 `backend/api` 目录执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

请在本地 `.env` 中替换数据库凭据；`.env` 不应提交。默认生产型连接使用 `postgresql+asyncpg`。

生产环境必须显式设置高熵 `AUTH_SECRET_KEY`；缺失时应用拒绝启动。登录成功后后端设置名为 `ai_ops_session` 的签名 JWT 会话 Cookie，不在响应体返回 Token。Cookie 始终为 HttpOnly，SameSite 由 `AUTH_COOKIE_SAMESITE` 配置，并在 staging、production、experiment 环境强制设置 Secure。JWT 只保存用户 ID、Token 版本和授权修订号，不保存权限快照。授权变更使旧会话立即失效，注销会递增 Token 版本并删除 Cookie。

## Run

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`

应用启动不自动迁移数据库。数据库不可连接时进程仍可存活，但 readiness 返回 HTTP 503。

## DeepSeek Provider

DeepSeek 通过 `RoutedCapabilityGateway` 注册为 `deepseek.chat`，尚未连接选品、利润复核或 Listing 业务流程。本地 `.env` 配置：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_CONNECT_TIMEOUT_SECONDS=5
DEEPSEEK_REQUEST_TIMEOUT_SECONDS=30
DEEPSEEK_MAX_RETRIES=2
```

API Key、Base URL 和模型由 `SecretStr` 读取。Provider 对连接/请求分别设置超时，只对超时、网络错误、HTTP 429 和服务端错误进行有限重试；鉴权和请求结构错误不重试。请求提示词、Authorization Header 和密钥不写入日志、错误响应或审计。

拥有 admin 板块及 `capability.read` 权限的管理员可以检查连接状态：

```http
GET /api/v1/admin/capabilities/deepseek/status
```

状态响应只包含是否配置、是否可达、状态、主机名、模型、耗时和安全错误码，不返回密钥或请求头。普通测试使用 Mock；真实联网测试必须显式开启：

```powershell
$env:RUN_DEEPSEEK_LIVE_TESTS='1'
pytest tests/test_deepseek_provider.py::test_live_deepseek_chat_provider
Remove-Item Env:RUN_DEEPSEEK_LIVE_TESTS
```

## Authentication and role workspaces

```http
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/me
GET  /api/v1/me/access-context
GET  /api/v1/me/modules
GET  /api/v1/me/stores
GET  /api/v1/dashboard/summary
GET  /api/v1/operations/dashboard
GET  /api/v1/procurement/dashboard
GET  /api/v1/creative/dashboard
GET  /api/v1/admin/dashboard
GET  /api/v1/operations/projects
GET  /api/v1/procurement/purchase-requests
GET  /api/v1/creative/content-tasks
GET  /api/v1/admin/errors
GET  /api/v1/admin/ai-feedback
GET  /api/v1/admin/audit-logs
GET  /api/v1/admin/capabilities/deepseek/status
GET  /api/v1/selection-skills
GET  /api/v1/selection-skills/{skill_key}
GET  /api/v1/admin/users
GET  /api/v1/admin/users/{user_id}
PUT  /api/v1/admin/users/{user_id}/roles
PUT  /api/v1/admin/users/{user_id}/modules
PUT  /api/v1/admin/users/{user_id}/store-scopes
GET  /api/v1/admin/stores
POST /api/v1/admin/stores
PATCH /api/v1/admin/stores/{store_id}
```

登录请求只接受 `username` 和 `password`，不接受角色、板块或店铺参数。`POST /auth/login`、`GET /me` 和 `GET /me/access-context` 返回同一种访问上下文结构；浏览器通过 `credentials: include` 自动携带 HttpOnly Cookie。后端从数据库解析完整访问上下文。密码使用 Argon2 哈希。受保护路由同时声明 Module 和 Permission 依赖；应用服务再次执行对象 Scope 检查。运营查询在 SQL 层强制按授权店铺过滤。店铺 API 不接收凭证，只返回 `credential_configured`；数据库中的 `credential_ref` 仅允许保存安全存储引用。

```json
{
  "user": {
    "user_id": "...",
    "username": "operations_demo",
    "display_name": "Operations Demo (DEMO)"
  },
  "roles": ["operations"],
  "modules": ["operations"],
  "permissions": ["operations.dashboard.read"],
  "scopes": {"organization_ids": [], "team_ids": [], "store_ids": ["..."]},
  "default_landing": "/operations",
  "authorization_revision": 1
}
```

内置角色：

| Role | 数据范围 |
|---|---|
| operations | 仅管理员分配店铺内的运营项目与任务 |
| procurement | 采购模块内本人、团队、店铺或组织授权范围 |
| creative | 分配给本人或所属美工团队的内容任务与素材 |
| admin | 所有业务只读范围、错误、AI 反馈和审计；敏感读取仍审计 |

Listing 文案使用独立动作权限 `listing_copy.read/generate/edit/review/history.read`。这些权限默认只授予运营角色；采购角色无 Listing 文案权限。管理员角色也不默认继承这些权限，必须通过账号直接权限显式授予。所有文案读取仍执行店铺范围过滤。

AI 选品表导出使用独立动作权限 `selection.export`，采购询价表导出使用 `quotation.export`。两者都不随普通读取权限自动授予，管理员也必须显式获得对应阶段的导出权限。`quotation.export` 只允许采购板块或显式监管的管理员使用，运营板块即使被错误分配该权限也不能导出供应商及报价数据。导出接口为：

```text
POST /api/v1/selection-exports
GET  /api/v1/selection-exports/{export_id}
GET  /api/v1/selection-exports/{export_id}/download
```

当前接受 `stage=initial_selection|quotation`。询价导出默认且仅包含每条候选最新的 `submitted` 版本；当前没有草稿导出参数。创建时在 PostgreSQL 内冻结整表快照及快照行，随后使用 `openpyxl` 只写模式生成 `.xlsx`。下载会重新校验当前账号、阶段动作权限、任务所有人和冻结的店铺/组织范围。响应不返回服务器路径。

开发文件默认保存在仓库的 `tmp/exports/`，由 `EXPORT_STORAGE_PATH` 配置；这是可清理的私有临时目录，不是正式代码或公开静态目录。`EXPORT_FILE_TTL_HOURS` 默认 24 小时。文件过期后可清理，但 `selection_export_jobs`、快照引用、审计和校验和应继续保留。当前版本尚未提供自动清理 Worker。

当前用户名/密码认证通过 `AuthenticationService` 和仓储协议隔离。企业身份方案确认后可替换为 OIDC/SSO，而不改变路由授权和 Scope 模型。

## Selection Skill registry

六个 Amazon 选品 Skill 以不可变 bundle 和逐文件 SHA-256 登记在 `ai/skills/amazon-selection/`。列表与详情接口只返回安全元数据、启动参数定义、规则版本和输出 JSON Schema，不读取或返回完整 Skill 正文。采购账号需同时拥有 procurement 板块和 `selection.read`；管理员需同时拥有 admin 板块和 `all_business.read`。接口不接收客户端文件路径或店铺范围，也不会创建选品任务。

`SELECTION_SKILL_ASSETS_PATH` 可配置服务器端受控根目录。默认值为 `../../ai/skills/amazon-selection`。当前六项状态均为 `registered_not_executable`，不会调用 DeepSeek 或 Sorftime MCP。

## Development demo users

四个演示账号只可由本地命令在 `local` 或 `test` 环境显式创建，不会在应用启动或生产迁移时自动创建：

在 `.env` 中设置四个 `DEMO_*_PASSWORD` 后运行：

```powershell
python scripts/seed_demo_users.py
python scripts/verify_database.py
```

账号为 `operations_demo`、`procurement_demo`、`creative_demo`、`admin_demo`。密码只从 `.env`/环境变量读取，不在源码、迁移或契约中保存。种子脚本可重复执行：它会校正四个开发账号的角色、板块和演示店铺范围，但不会创建重复账号；密码变化时使旧会话失效。脚本在 staging/production 环境会直接拒绝执行。

## Database and migrations

API 数据访问使用 SQLAlchemy 异步引擎和 `asyncpg`。数据库用例通过 `get_db_session` 获得一次请求独占的 `AsyncSession`；Session 不跨请求或并发任务共享，异常时回滚并在作用域结束时关闭。提交由应用服务的事务边界显式完成。

本地 PostgreSQL 推荐使用独立数据库和应用账号。以下命令需要 PostgreSQL 管理员密码，示例密码必须替换为 `.env` 中仅本机保存的值：

```sql
CREATE ROLE ai_product_ops_app LOGIN PASSWORD '<local-app-password>';
CREATE DATABASE ai_product_ops_dev OWNER ai_product_ops_app;
```

然后将 URL 编码后的密码写入 `.env`：

```text
DATABASE_URL=postgresql+asyncpg://ai_product_ops_app:<url-encoded-password>@127.0.0.1:5432/ai_product_ops_dev
```

以后需要轮换应用数据库密码时，可让脚本生成随机密码并同步 `.env`：

```powershell
python scripts/rotate_local_database_password.py
```

如需指定新密码，通过临时环境变量传入，执行后立即清除：

```powershell
$env:NEW_DATABASE_PASSWORD='your-new-local-password'
python scripts/rotate_local_database_password.py
Remove-Item Env:NEW_DATABASE_PASSWORD
```

执行结构迁移、开发数据和数据库验证：

```powershell
alembic upgrade head
python scripts/seed_demo_users.py
python scripts/verify_database.py
alembic current
```

迁移 `0001` 建立 Outbox 与幂等记录扩展表；`0002` 建立 IAM、岗位范围读模型、错误、AI 反馈与追加式审计表；`0003` 增加账号板块、直接权限、规范化店铺范围和授权修订号。迁移不会创建演示用户。

## Quality checks

测试使用内存 SQLite 配置和替代健康探针，不要求 PostgreSQL：

```powershell
pytest
ruff check .
mypy app scripts
```

### Isolated PostgreSQL integration tests

Real PostgreSQL tests must use a dedicated database. They never reuse `DATABASE_URL` and never
fall back to the development database when `TEST_DATABASE_URL` is missing. Recommended local
configuration in the untracked `.env`:

```ini
RUN_POSTGRESQL_INTEGRATION_TESTS=0
TEST_DATABASE_URL=postgresql+asyncpg://ai_product_ops_app:<url-encoded-password>@127.0.0.1:5432/ai_product_ops_test
```

Create `ai_product_ops_test` once with a PostgreSQL administrator, then prepare and run it:

```powershell
$env:RUN_POSTGRESQL_INTEGRATION_TESTS='1'
python -m scripts.prepare_postgresql_test_database
pytest -q -rs
Remove-Item Env:RUN_POSTGRESQL_INTEGRATION_TESTS
```

The test entry gate requires a PostgreSQL database whose name ends in `_test`. It rejects
`ai_product_ops_dev`, `postgres`, `template0`, `template1`, staging/production targets, and a target
identical to `DATABASE_URL` before collection or fixture writes. Error messages contain only safe
host/database identifiers. Detailed setup and safety rules are in `tests/README.md`.

重新导出共享契约：

```powershell
python scripts/export_contracts.py
```

## Architecture boundaries

- Router 仅做 HTTP 协议转换和依赖注入。
- Application service 编排用例；Repository protocol 隔离数据来源。
- 领域模型不依赖 ORM。
- SQLAlchemy、配置、日志和中间件属于基础设施层。
- `app/modules/registry.py` 登记 identity、authorization、product、project、selection、quotation、procurement、content、listing、workflow、approval、capability/MCP 和 audit 边界。
- AI/MCP 未来只能经能力网关接入；ERP 仍是采购、库存和发运事实来源。
- `CapabilityGateway`、`MCPClientAdapter`、`MarketplaceConnector`、`ERPConnector` 和 `StoreCredentialProvider` 是预留端口；未来调用必须携带用户、板块、店铺、权限范围及 Task/Run/Action 上下文。
- 任何未来外部写入必须建立 `task_id -> run_id -> action_id -> external_receipt_id` 链路，并通过权限、审批、幂等、Outbox 和回查机制。

