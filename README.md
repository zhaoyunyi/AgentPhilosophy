# AgentPhilosophy

把共享的 Agent 协作规则、Spec 和项目级 skills 按配置同步到各个项目，让项目保留自己的定制，同时持续采用经过发布的更新。

适合维护多个项目的开发者，也适合独立接入的开源使用者。每个项目自行选择模块与升级时机，无需访问维护者的电脑或本机 registry。默认生成仓库级 `skills/` 与 Codex 项目级 `.agents/skills/`；其他宿主与历史目录见 [配置指南](docs/cli/configuration.md)。

历史使用者请先阅读 [历史清理与重新接入](docs/history-cleanup.md)：2026-11-10 清理后提交 SHA 与发布附件摘要已变化，版本号保留。

## 从哪里开始

| 你的任务 | 入口 |
| --- | --- |
| 第一次接入 | 下方快速开始；已有规则先走迁移 |
| 已接入，想升级 | [一句话升级与手动 CLI](docs/cli/upgrade.md) |
| 选择 skills、了解用途 | [全部技能：安装与使用](docs/cli/skills.md) |
| 保留项目定制、处理冲突 | [配置与 custom](docs/cli/configuration.md)、[安全边界](docs/cli/safety.md) |
| 维护中央内容或贡献代码 | [维护入口](docs/agents/maintenance.md)、[完整文档索引](docs/README.md) |

## 快速开始

前提：安装 uv、Git，Python 版本至少 3.12。安装已经发布的稳定版本：

```bash
uv tool install git+https://github.com/zhaoyunyi/AgentPhilosophy.git@v1.3.0
agentphilosophy-sync --version
agentphilosophy-sync validate
```

默认使用安装包自带的规范源。安装包含 `code-review-graph==2.3.9` 及同名 CLI；其首次配置、MCP 和资源成本见 [使用指南](docs/guides/code-review-graph.md)。

**新项目**选择适合的 preset，检查预览后应用：

```bash
agentphilosophy-sync init /path/to/project --preset fullstack
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
agentphilosophy-sync status --project /path/to/project
```

`fullstack`、`frontend`、`mobile-sdk`、`orchestrator` 的差异见 [目标配置](docs/cli/configuration.md)。默认 preset 包含 jj 协作规则；采用这些规则的项目需要准备 jj。交互选择可使用 `init --interactive`；它只生成配置，不自动同步文件。

**已有 `AGENTS.md`、Spec 或 skills 的项目**先盘点，阅读报告后接管，避免覆盖自己的内容：

```bash
agentphilosophy-sync migrate /path/to/project
```

接着按 [老项目迁移指南](docs/cli/migration.md) 检查候选配置、确认接管范围，再 validate、adopt、预览和应用。已有 `.agentphilosophy.yaml` 的项目直接使用原配置，不重跑初始化。

## 已接入，如何升级

默认对 Agent 说：

> 升级本项目的 AgentPhilosophy 到最新正式稳定版。保留已有模块选择和项目定制，兼容且无冲突时完成升级与验证；新增模块给出建议，不兼容迁移或手改冲突时说明影响。保留回退 ID。

升级流程是：**发现正式版本 → 固定版本及源码提交 → 预览差异 → 保存回退点 → 应用并验证**。新增模块不会自动加入项目，已有 custom 和无关工作应保留。

**版本要求：这套 `check-update / upgrade / rollback` 流程从正式版 1.3.0 开始提供。** v1.2.2 及更早用户先按上方稳定安装命令更新 CLI 一次；这一步不会自动同步项目内容。完整的手动命令、首次引导、冲突处理和恢复步骤见 [升级与回退指南](docs/cli/upgrade.md)。

工具安装、项目内容同步、采用新模块是三个独立动作。CLI、内容源、模块也各自记录版本；`status` 只比较当前本地源，联网发现 Release 使用新版 `check-update`。详见 [版本与更新判断](docs/cli/versions.md)。

发布内容与兼容说明统一从 [GitHub Releases](https://github.com/zhaoyunyi/AgentPhilosophy/releases) 和 [release-notes/README.md](release-notes/README.md) 查询。

## 给 Agent 的文档入口

```bash
agentphilosophy-sync llm-usage
agentphilosophy-sync llm-usage --mode auto-config
agentphilosophy-sync llm-usage --mode user-breakpoints --format json
```

完整入口按任务索引组装当前实现的说明；`auto-config` 用于已有自动配置授权的接入，`user-breakpoints` 用于需要用户选择模块和目录的接入。升级已有项目使用升级 skill 和升级指南，保留当前选择。

项目特有规则放在 `.agents/custom`，托管文件与 state 通过 CLI 生成。默认 `loop-check` 提供仓库巡检能力，但安装 skill 不会自动建立定时任务。更多指南见 [docs/README.md](docs/README.md)。

## 维护与贡献

```bash
git clone https://github.com/zhaoyunyi/AgentPhilosophy.git
cd AgentPhilosophy
uv run --locked sync.py validate
uv run --locked pytest -q
```

源码可能领先于稳定 Release。需要自定义源或开发内容时显式选择源码流程，并保留版本与来源记录。

- 修改 CLI、模块、模板或同步 skill：[中央源维护入口](docs/agents/maintenance.md)。
- 发版、制品回执及下游兼容承诺：[发布流程](docs/release-process.md)。
- 本机多个项目的登记与批量同步：[Registry 指南](docs/cli/registry.md)。`registry.yaml` 只保存在本机，复用模板是 `registry.example.yaml`。
- 批量同步后的项目文档更新：[CLI 命令](docs/cli/commands.md)；需显式声明 `documentation_paths` 和受限模型命令。
- Agent 导航与项目约定：[docs/agents/README.md](docs/agents/README.md)、[AGENTS.md](AGENTS.md)。
