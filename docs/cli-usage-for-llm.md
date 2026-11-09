# AgentPhilosophy CLI 使用说明（给 LLM）

本入口按任务路由，先读相关页面；以当前 CLI `--help` 和实现为准。`llm-usage` 会按下方清单组装完整说明，旧单页内容源也继续支持。

| 任务 | 读取页面 |
| --- | --- |
| 全部技能、安装模块、调用示例与排障 | [skills](cli/skills.md) |
| 运行前提 | [runtime](cli/runtime.md) |
| 真实可用命令 | [commands](cli/commands.md) |
| 版本与更新判断 | [versions](cli/versions.md) |
| 已接入项目升级、发现正式版本和回退 | [upgrade](cli/upgrade.md) |
| 目标项目配置 | [configuration](cli/configuration.md) |
| Superpowers 显式可选合同 | [superpowers](cli/superpowers.md) |
| Portless 本地开发入口 | [portless](cli/portless.md) |
| Ponytail 精简编码 skill | [ponytail](cli/ponytail.md) |
| Reverse Skill 授权逆向路由 skill | [reverse-skill](cli/reverse-skill.md) |
| 架构加深评审 skill | [architecture-review](cli/architecture-review.md) |
| 独立 code-review 审查 skill | [code-review](cli/code-review.md) |
| code-review-graph 结构图谱依赖 | [code-review-graph](cli/code-review-graph.md) |
| Matt Pocock 完整工程 skill 家族 | [matt-skills](cli/matt-skills.md) |
| Agent 哲学决策框架 | [philosophy](cli/philosophy.md) |
| 仓库日常巡检与自动修复 | [loop-check](cli/loop-check.md) |
| 构建流水线调优 skill | [build-pipeline](cli/build-pipeline.md) |
| Grok CLI headless 编排 skill | [grok-cli](cli/grok-cli.md) |
| Registry 文件 | [registry](cli/registry.md) |
| 新项目接入流程 | [new-project](cli/new-project.md) |
| 老项目迁移流程 | [migration](cli/migration.md) |
| 安全边界 | [safety](cli/safety.md) |
| LLM 执行规则 | [agent-execution](cli/agent-execution.md) |

第一次接入或选择技能，先读 [全部技能指南](cli/skills.md)：覆盖技能到安装模块的映射、默认 preset、显式/自动调用、完整安装步骤与每项请求示例。从精简模式导航时保留原执行环境、工作目录、CLI/uv 前缀与 `--source`，只去掉 `--mode`/`--format`。安装版默认源的完整入口是 `agentphilosophy-sync llm-usage`。

修改 CLI 文档时更新对应单页；本清单同时决定完整输出的顺序，避免复制正文。

<!-- include: cli/skills.md -->
<!-- include: cli/runtime.md -->
<!-- include: cli/commands.md -->
<!-- include: cli/versions.md -->
<!-- include: cli/upgrade.md -->
<!-- include: cli/configuration.md -->
<!-- include: cli/superpowers.md -->
<!-- include: cli/portless.md -->
<!-- include: cli/ponytail.md -->
<!-- include: cli/reverse-skill.md -->
<!-- include: cli/architecture-review.md -->
<!-- include: cli/code-review.md -->
<!-- include: cli/code-review-graph.md -->
<!-- include: cli/matt-skills.md -->
<!-- include: cli/philosophy.md -->
<!-- include: cli/loop-check.md -->
<!-- include: cli/build-pipeline.md -->
<!-- include: cli/grok-cli.md -->
<!-- include: cli/registry.md -->
<!-- include: cli/new-project.md -->
<!-- include: cli/migration.md -->
<!-- include: cli/safety.md -->
<!-- include: cli/agent-execution.md -->
