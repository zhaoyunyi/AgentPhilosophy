## 三、版本与更新判断

AgentPhilosophy 使用三层版本判断目标项目是否需要更新：

- CLI 工具版本来自 `pyproject.toml` 和 `agentphilosophy.__version__`，只表示同步程序自身版本。
- 中央规范内容源版本来自 `catalog.yaml` 的 `content_version`，用于判断依赖项目是否需要同步新一轮中央内容。
- 单个模块版本来自各 `module.yaml` 的 `version`，用于判断具体模块是否 stale。
- 外部来源 skill 的上游锁定版本来自各 `module.yaml` 的 `upstream.repository`、`upstream.ref`、`upstream.revision` 和 `upstream.tracked_paths`，用于维护者判断是否需要跟进上游变化。

`agentphilosophy-sync --version` 用于确认当前安装的 CLI release 版本。`push --apply` 和 `adopt` 会把当前 `agentphilosophy_version` 与 `source_content_version` 写入目标项目 `.agents/agentphilosophy-state.yaml`；`status --project` 如果发现 state 中 CLI 版本落后于当前安装包，会输出 `agentphilosophy_version stale: <old> -> <new>`，如果发现内容源版本落后于当前中央源，会输出 `source_content_version stale: <old> -> <new>`。看到 stale 提示时，先运行 `push /path/to/project --dry-run` 审查计划，再决定是否 `--apply`。

如果 state 中的版本高于当前中央源或当前 CLI，`status` 会提示 `source_content_version newer than current source` 或 `agentphilosophy_version newer than current CLI`；此时先检查是否误用了旧的 `--source`、旧安装包或回退后的中央源，不要直接覆盖目标项目。`source_tree_hash` 是源文件指纹，`catalog.yaml` 变更可能同时触发 hash drift 和内容版本提示。
