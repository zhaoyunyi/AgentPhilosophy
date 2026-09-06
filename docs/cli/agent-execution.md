## 二十、LLM 执行规则

- 操作前先运行 `uv run sync.py validate`，确认中央源有效。
- 对目标项目写入前必须先运行 `push --dry-run`。
- 在目标项目新增、迁移或沉淀长期有效文档时，必须同时检查主 `AGENTS.md` 或其 layered custom 源是否索引该文档或目录；`docs/` 下的指南、运维记录、问题复盘和部署说明还应更新项目文档索引，例如 `docs/README.md`。若 `AGENTS.md` 是 AgentPhilosophy layered 输出，优先写 `.agents/custom/AGENTS.custom.md` 后再 `push --apply`，不要直接手工改托管结果。
- 读取 `aphilosophy/` 文档应按场景触发，不要把它们当成每次任务的必读上下文。
- 执行可选参数前先看对应 `--help`；帮助里没有的参数不要执行。
- 如果 CLI 输出 `[error]`，停止写入并回报具体错误。
- 如果 CLI 输出 `[warning]`，继续前先判断 warning 是否影响本次目标。
- 不要手工编辑 `.agents/agentphilosophy-state.yaml`。
- 不要把未来设计当成当前能力。
