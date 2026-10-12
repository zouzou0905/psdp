# Identity and authorization schema

## Boundaries

- `iam_users` 保存账号状态、Argon2 密码哈希、Token 版本、授权修订号和组织/团队 Scope。禁止保存明文密码或 Token。
- Role 与 Permission 为多对多关系；`iam_user_permissions` 保存账号直接权限，授权判断不只检查角色名。
- `iam_modules` 与 `iam_user_modules` 独立保存账号可见板块，不能由客户端自行选择。
- `stores` 保存非敏感店铺元数据，`credential_ref` 只能是不透明安全存储引用；`iam_user_store_scopes` 保存规范化账号店铺范围。
- Access Token 不携带权限快照，只携带用户、Token 版本和授权修订号。每次认证从 IAM 仓储获取当前角色、板块、权限和 Scope。
- `workspace_records` 是首版可替换的岗位读模型。列表和按 ID 查询都必须在 SQL `WHERE` 中施加 Scope。
- `governance_audit_logs` 为追加写。普通应用仓储不暴露 update/delete。
- `governance_error_records` 与 `ai_feedback_records` 分表，避免混淆系统故障与业务纠错反馈。

## Scope policy

| Workspace | SQL scope |
|---|---|
| operations | 强制 `store_id IN authorized_store_ids`；空范围返回空集 |
| procurement | assignee/owner OR organization OR team OR store |
| creative | assignee/owner OR team |
| admin | `all_business.read` 可读取全部只读记录 |

Scope 授权不等于高风险动作审批。管理员权限不会使采购、发布或外部写入绕过审批、输入版本校验或 Task/Run/Action/Receipt 链路。
