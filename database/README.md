# Database

数据库的可执行 Alembic 环境位于 `backend/api/alembic/`，以便与 Python 包和 SQLAlchemy metadata 使用同一版本依赖。`database/` 保留跨服务的数据字典、Schema 设计和种子数据。

当前初始迁移仅创建：

- `workflow_outbox_events`：事务 Outbox 的持久化扩展位置。
- `workflow_idempotency_records`：未来写命令的幂等记录扩展位置。

第二个迁移增加：

- `iam_users`、`iam_roles`、`iam_permissions`、`iam_user_roles`、`iam_role_permissions`
- `workspace_records`：首版岗位范围读模型，后续由正式领域表替换
- `governance_error_records`：系统/API/Worker/集成错误
- `ai_feedback_records`：与系统错误分离的 AI 反馈
- `governance_audit_logs`：只追加审计事件；应用不提供更新或删除仓储方法

PostgreSQL 是正式业务主库。Redis/Celery 状态不是业务事实来源。

