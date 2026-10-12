# Worker Boundaries

首版预留四类独立执行边界，不在本阶段启动 Celery 或连接真实外部系统：

- `orchestration`：任务调度、超时、重试与补偿。
- `ai`：经未来能力网关执行文本、图像和评测任务。
- `external-actions`：审批后 ERP/Marketplace 外部写入；与普通 Worker 分权部署。
- `reconciliation`：未知结果回查与差异对账，禁止盲目重试外部写入。

每个 Worker 任务必须创建独立 `AsyncSession`。PostgreSQL 持久化 Task/Run/Action、审批、Outbox、幂等和回执；Redis/Celery 仅承担传输与调度，不是正式状态来源。任何未来外部写入都必须完整关联 `task_id -> run_id -> action_id -> external_receipt_id`。

