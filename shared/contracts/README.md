# Shared API Contracts

这些文件由后端的 Pydantic/OpenAPI 模型导出，供前端和契约测试使用：

- `openapi.v1.json`：完整 v1 HTTP/OpenAPI 契约。
- `dashboard-summary.schema.json`：Dashboard 响应 JSON Schema。
- `dashboard-summary.example.json`：安全的空演示响应；不是正式经营事实。
- `current-user.example.json`：`GET /me` 的账号访问上下文，与登录响应结构一致。
- `login.example.json`：账号密码登录、访问上下文响应以及 HttpOnly Cookie 属性；响应体不包含 Token。
- `access-context.example.json`：账号派生的角色、可见板块、动作权限、数据范围及授权修订号。
- `modules.example.json`：当前账号可见板块和后端决定的默认落点。
- `stores.example.json`：当前账号或管理员可见的店铺；只暴露是否已配置凭证，不返回凭证引用。
- `admin-user-access.example.json`：管理员查看账号授权配置。
- `admin-users.example.json`：管理员用户列表响应，不包含密码、哈希或会话 Token。
- `admin-access-updates.example.json`：角色/动作权限、板块和店铺范围更新请求。
- `admin-user-create.example.json`：管理员创建无初始授权账号的请求与安全响应示例。
- `admin-user-status.example.json`：管理员启用、停用账号的端点与响应示例。
- `permission-error.example.json`：统一 403 权限错误。
- `admin-errors.example.json`：已脱敏的管理员错误列表。
- `ai-feedback.example.json`：AI 反馈列表。
- `audit-logs.example.json`：追加式审计日志列表。
- `selection-flow.example.json`：同一选品记录关联询价、最终复选和三条竞品的请求示例。
- `selection-ai-task.example.json`：AI 初选、利润复核和 Listing 草稿的异步任务边界；示例不代表任务已成功执行。
- `deepseek-status.example.json`：管理员 DeepSeek 连接状态响应，不包含密钥或 Authorization Header。
- `listing-copy-permissions.example.json`：运营专属 Listing 文案动作权限；采购和管理员默认均不具备。
- `selection-export.example.json`：AI 选品表与采购询价表的冻结快照任务、受控下载、阶段权限及正式询价过滤示例。
- `selection-skills.example.json`：六个只读 Skill 卡片与安全详情示例，不包含 Skill 正文和服务器路径。
- `selection-candidate-output.schema.json`：公共候选字段及六个独立扩展对象的 JSON Schema 骨架。

在 `backend/api` 中运行 `python scripts/export_contracts.py` 可重新生成。生成时间示例固定，避免无意义 diff。

