# ADR-001：核心后端采用 FastAPI

- 状态：已确认
- 日期：2026-10-06
- 决策人：项目负责人

## 背景

AI 商品运营中台需要承载商品、经营项目、选品、采购、内容、Listing、任务、审批、版本和审计等核心业务，同时需要接入 AI 能力、MCP 与其他外部应用。

## 决策

核心后端直接使用 Python 3.12+ 与 FastAPI，不采用 NestJS 作为核心业务 API。

配套技术基线：

- Pydantic v2：请求、响应和跨模块数据契约。
- SQLAlchemy 2.x：数据访问与事务。
- Alembic：数据库迁移。
- PostgreSQL：核心业务主库。
- Redis + Celery：首版异步任务、重试与调度；持久业务状态仍写入 PostgreSQL。
- Uvicorn：ASGI 应用服务器，由进程管理器或容器编排负责多进程和横向扩展。

## 约束

- FastAPI 路由不得直接承载领域规则或直接修改 ORM 对象。
- 业务逻辑进入应用服务与领域层，数据库访问通过仓储接口。
- 每个请求或 Worker 任务使用独立的 SQLAlchemy `AsyncSession`。
- Celery/Redis 不作为任务事实来源；`task_id`、`run_id`、`action_id`、状态和回执持久化到 PostgreSQL。
- AI/MCP 调用必须经过能力网关、权限检查、版本记录和审计，不得从路由层直接调用生产写工具。
- 高风险动作仍需后端授权与审批，技术栈选择不改变项目治理边界。

## 影响

正面影响：

- 核心业务与 AI/数据处理使用同一语言生态。
- Pydantic 模型可统一 API、任务和能力契约。
- 便于接入 Python AI SDK、评测工具和 MCP 客户端。

需要控制的风险：

- CPU 密集任务不能阻塞 API 进程，应交给独立 Worker。
- 必须保持模块化边界，避免演变为路由、ORM 与业务规则混杂的脚本式项目。
- Celery 为至少一次投递语义，消费者必须依据事件 ID 或动作 ID 实现幂等。

## 后续动作

- 数据库详细设计统一采用 SQLAlchemy/Alembic 表达。
- API 项目骨架按模块化 FastAPI 结构创建。
- 在实施阶段确定 Celery + Redis 是否足以支撑首版长流程，必要时另行评估持久化工作流引擎。
