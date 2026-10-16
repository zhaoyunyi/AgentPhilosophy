# AgentPhilosophy 文档索引

本索引用于定位 `docs/` 下长期有效的项目文档。新增、迁移或沉淀长期文档时，必须在同一轮改动中更新本文件；测试会检查每个 `docs/**/*.md` 是否出现在这里，避免正文有变更但没有入口。

## Agent 导航

- [docs/agents/README.md](agents/README.md)：Matt skills 项目级 setup 与统一读取入口。
- [docs/agents/issue-tracker.md](agents/issue-tracker.md)：GitHub issue 与 Wayfinder 约定。
- [docs/agents/triage-labels.md](agents/triage-labels.md)：稳定 triage 标签语义。
- [docs/agents/domain.md](agents/domain.md)：领域、架构和代码的读取顺序。
- [docs/agents/out-of-scope/README.md](agents/out-of-scope/README.md)：明确排除项的记录边界。

- [docs/agents/maintenance.md](agents/maintenance.md)：中央源修改、镜像刷新、验证与兼容边界。
- [docs/agents/skill-routing.md](agents/skill-routing.md)：技能选择的正例、反例、相似任务与验收边界。

## CLI 与同步说明

- [docs/cli-usage-for-llm.md](cli-usage-for-llm.md)：给 LLM 或自动化 agent 的完整 CLI 操作说明，覆盖接入、迁移、同步、可选模块和写入前校验。
- [docs/llm-usage-auto-config.md](llm-usage-auto-config.md)：用户授权 agent 自动判断接入方案时使用的精简协议。
- [docs/llm-usage-user-breakpoints.md](llm-usage-user-breakpoints.md)：需要用户选择 preset、模块或路径时使用的断点协议。
- [docs/llm-usage-user-breakpoints.json](llm-usage-user-breakpoints.json)：用户断点协议的机器可读结构，供 agent 直接解析选项和回复格式。

## 发布与运维

- [docs/release-process.md](release-process.md)：AgentPhilosophy CLI 和中央内容源的发版、版本口径、发布校验和依赖项目更新判断。
- [release-notes/README.md](../release-notes/README.md)：正式版本发布说明的长期索引、命名约定和维护规则。

## 指南

- [spec/TestStrategy.md](../spec/TestStrategy.md)：编写测试注意事项、行为断言、BDD 场景先行与测试分层。
- [spec/BDDSpec.md](../spec/BDDSpec.md)：以 `user` 开头的 Given / When / Then 验收场景规范。
- [docs/guides/aphilosophy-methodology.md](guides/aphilosophy-methodology.md)：维护或扩展 `aphilosophy/` 决策框架时使用的方法论和成果索引。
- [docs/guides/mattpocock-engineering-flow.md](guides/mattpocock-engineering-flow.md)：Matt Pocock 27 个活跃 skills 的完整能力集、`docs/agents/` 设置目录、AgentPhilosophy 托管边界和主线/分支用法。
- [docs/guides/value-specification-audit.md](guides/value-specification-audit.md)：面向开发者的价值规约审计指南，用于检查规则本身是否可信。
- [docs/guides/code-review-graph.md](guides/code-review-graph.md)：`code-review-graph` 依赖、Skill、MCP 和 CLI 的职责分层、Codex 配置与常用工作流。

## 设计与计划

- [docs/plans/2026-05-10-agent-philosophy-design.md](plans/2026-05-10-agent-philosophy-design.md)：AgentPhilosophy 统一 Agent 规范管理系统的设计文档。
- [docs/superpowers/specs/2026-07-13-batch-sync-llm-documentation-design.md](superpowers/specs/2026-07-13-batch-sync-llm-documentation-design.md)：依赖项目批量同步版本后，按显式文档范围调用大模型更新项目自有文档的设计与安全边界。
- [docs/superpowers/specs/2026-07-13-flexible-multi-agent-and-optional-superpowers-design.md](superpowers/specs/2026-07-13-flexible-multi-agent-and-optional-superpowers-design.md)：灵活选择多 Agent 模型与推理强度，并将 Superpowers 调整为项目显式可选模块的设计。
- [docs/superpowers/plans/2026-07-13-flexible-multi-agent-and-optional-superpowers.md](superpowers/plans/2026-07-13-flexible-multi-agent-and-optional-superpowers.md)：按测试先行拆分多 Agent 规则、Superpowers 可选默认、LLM 合同和 0.7.7 本地 release 的实施步骤。
- [docs/superpowers/specs/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-design.md](superpowers/specs/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-design.md)：AgentPhilosophy 0.7.5 模板发布、默认 preset skill 刷新与 cadraq 无漂移同步设计。
- [docs/superpowers/plans/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-implementation.md](superpowers/plans/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-implementation.md)：AgentPhilosophy 0.7.5 模板扩展、发布、cadraq 同步与验证执行计划。

## CLI 按任务读取

- [docs/cli/agent-execution.md](cli/agent-execution.md)：LLM 执行规则。
- [docs/cli/architecture-review.md](cli/architecture-review.md)：架构加深评审 skill。
- [docs/cli/build-pipeline.md](cli/build-pipeline.md)：构建流水线调优 skill 1.1.0：测试隔离、I/O/缓存、预装工具、完整案例及只读比较器。
- [docs/cli/code-review-graph.md](cli/code-review-graph.md)：code-review-graph 结构图谱依赖。
- [docs/cli/code-review.md](cli/code-review.md)：独立 code-review 审查 skill。
- [docs/cli/commands.md](cli/commands.md)：真实可用命令。
- [docs/cli/configuration.md](cli/configuration.md)：目标项目配置。
- [docs/cli/loop-check.md](cli/loop-check.md)：仓库巡检计划、触发、自动修复 PR 和统一退役追溯。
- [docs/cli/grok-cli.md](cli/grok-cli.md)：Grok CLI headless 编排 skill。
- [docs/cli/matt-skills.md](cli/matt-skills.md)：Matt Pocock 完整工程 skill 家族。
- [docs/cli/migration.md](cli/migration.md)：老项目迁移流程。
- [docs/cli/new-project.md](cli/new-project.md)：新项目接入流程。
- [docs/cli/philosophy.md](cli/philosophy.md)：Agent 哲学决策框架。
- [docs/cli/ponytail.md](cli/ponytail.md)：Ponytail 精简编码 skill。
- [docs/cli/portless.md](cli/portless.md)：Portless 本地开发入口。
- [docs/cli/registry.md](cli/registry.md)：Registry 文件。
- [docs/cli/reverse-skill.md](cli/reverse-skill.md)：Reverse Skill 授权逆向路由 skill。
- [docs/cli/runtime.md](cli/runtime.md)：运行前提。
- [docs/cli/safety.md](cli/safety.md)：安全边界。
- [docs/cli/superpowers.md](cli/superpowers.md)：Superpowers 显式可选合同。
- [docs/cli/versions.md](cli/versions.md)：版本与更新判断。

- [docs/plans/2026-09-06-audit-remediation.md](plans/2026-09-06-audit-remediation.md)：本轮审查修复合同、上游筛选与验证结果。
