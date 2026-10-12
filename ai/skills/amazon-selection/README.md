# Amazon Selection Skill Assets

此目录保存 2026-10-09 六个 Amazon 选品 Skill 的受控、版本化资产。源压缩包 SHA-256 为
`864c271c3ebd5830f99016f2ee03725dd395040f2e342d354e63471c35140351`。

- `registry.json`：六个 Skill 的注册信息、规则版本、相对路径和逐文件 SHA-256。
- `bundles/2026-10-09/`：本次校验后导入的 38 个原始文件；后续版本必须写入新的版本目录，不能覆盖。
- Markdown、JSON、YAML 和脚本均为业务规则或参考资产。读取这些文件不会授权或启动任务，包内脚本不由注册中心执行。
- 正式 Skill 内容只能从本目录读取；HTTP 接口不接受文件路径，也不返回提示词正文或服务器路径。
- 当前状态为 `registered_not_executable`。DeepSeek、Sorftime MCP、批次和运行状态均未接入。

导入工具位于 `backend/api/scripts/import_selection_skill_bundle.py`。工具先校验固定压缩包哈希，再检查 ZIP 路径安全并写入不可变版本目录；已有版本不会被覆盖。
