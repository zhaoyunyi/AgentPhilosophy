# AgentPhilosophy Agent 导航

本目录是 Matt Pocock skills 的项目级 setup 层，把 issue、triage、领域资料和明确排除项接到 AgentPhilosophy 的 CLI、模块、模板、测试与发布文档。`docs/README.md` 仍是完整长期文档索引，本目录不复制或替代它。

## 推荐读取顺序

1. 根 `AGENTS.md`、`CLAUDE.md`、`README.md`。
2. `docs/README.md` 与 `docs/cli-usage-for-llm.md`。
3. 当前任务相关的模块资源、skill、CLI 实现和测试。
4. 涉及版本传播时再读 `docs/release-process.md` 与本机 `registry.yaml`。

## Matt setup 入口

- [Issue Tracker](issue-tracker.md)
- [Triage 标签](triage-labels.md)
- [领域资料](domain.md)
- [明确排除项](out-of-scope/README.md)

## 实现直达

- CLI 与同步实现：`src/agentphilosophy/`
- 托管模块：`modules/`
- 项目模板：`templates/`
- CLI 与回归测试：`tests/`
- Matt skills 原始导入与包装：`modules/skill-mattpocock-engineering/`
- 项目级 skills：`skills/`、`.codex/skills/`
- 依赖项目注册表：本机 `registry.yaml`（忽略提交，只作为本机同步真值）。
