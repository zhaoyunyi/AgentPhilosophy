---
name: agentphilosophy-sync
description: 使用或排查 AgentPhilosophy CLI 同步流程；适用于 agentphilosophy-sync、sync.py、.agentphilosophy.yaml、.agents/agentphilosophy-state.yaml、migrate/adopt/push/status、托管输出漂移和 .codex/skills discovery 收口任务。
---

# AgentPhilosophy sync

使用规则：

- 只在需要调用或排查 AgentPhilosophy 同步 CLI、托管输出、迁移接管、state 漂移或 `.codex/skills` discovery 收口时使用；普通 AGENTS、Spec 或 skill 内容审查优先按目标文件自己的规则处理。
- 如果当前目录是 AgentPhilosophy 源码仓库，先读 `docs/cli-usage-for-llm.md`，以当前已实现 CLI 为准。
- 如果在目标项目中，优先使用已安装的 `agentphilosophy-sync`；需要指定中央源码时使用 `uv run /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy ...`。
- 写入目标项目前必须先执行中央源校验和 dry-run：`validate` -> `validate /path/to/project` -> `push /path/to/project --dry-run` -> `push /path/to/project --apply`。
- 老项目先走 `migrate /path/to/project` 或 `migrate /path/to/project --write-config`，再检查迁移产物，随后 `adopt --from-report .agents/migration/adopt-plan.yaml`。
- 不要手工编辑 `.agents/agentphilosophy-state.yaml`；状态漂移通过 `push --dry-run`、`push --apply` 或 `status --project` 收口。
- 需要让 Codex 原生 skill discovery 自动触发时，确认 `skill_targets.codex_project` 指向 `.codex/skills`，并在 apply 后用 `find -L .codex/skills -name SKILL.md` 验证。
