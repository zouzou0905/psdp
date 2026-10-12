# 六个选品 Skill 注册中心

## 边界

本阶段只登记和只读查询 Skill 资产，不创建选品批次、任务或运行，不调用 DeepSeek、Sorftime MCP，也不改变选品、询价、利润或最终选品版本关系。压缩包中的文字和脚本是版本化参考资产，不是可自动执行的指令。

## 资产与版本

受控根目录为 `ai/skills/amazon-selection/`。`registry.json` 使用相对路径引用 `bundles/2026-10-09/` 下的不可变文件，并为 Skill 正文、类型规则和共享依赖保存 SHA-256。运行时加载注册表时会校验：

- 恰好存在六个批准的 `skill_key`，且不重复；
- 每个文件位于受控根目录内，不允许绝对路径、反斜线、盘符或 `..`；
- 每个依赖文件存在且当前 SHA-256 与登记值一致；
- `validated_variations` 必须依赖基础产品且不能用于新产品发现；
- `consumables_multipacks` 必须同时声明独立发现和标签复核模式。

新规则不能覆盖旧文件。应创建新的 bundle 目录、登记新的明确版本号和校验和，使未来运行能够继续引用原版本。

## 查询接口与授权

- `GET /api/v1/selection-skills`
- `GET /api/v1/selection-skills/{skill_key}`

接口复用 HttpOnly Cookie 会话及后端 `module + permission` 校验。当前允许采购板块且具备 `selection.read` 的账号，或管理员板块且具备 `all_business.read` 的账号读取。Skill 元数据不属于某一店铺的业务记录，因此接口不接收 `store_id`，也不会扩大当前账号的店铺范围。普通运营、美工和未登录访问分别返回 403 或 401。

列表返回六张卡片所需元数据；详情增加启动参数定义、规则版本、依赖校验和及输出 JSON Schema。响应不包含 Skill 正文、服务器文件路径、密钥、请求头或敏感配置。成功读取写入既有追加式审计日志。

## 输出契约

公共候选模型与六个独立 `extension` 模型仅定义可验证契约，不写入业务数据库。`null` 与数值 `0` 保持不同语义。未来执行层必须按 `skill_key` 选择对应扩展模型，不能把六类专属字段合并为固定超宽表。
