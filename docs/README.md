# AgentPhilosophy 文档索引

本索引用于定位 `docs/` 下长期有效的项目文档。新增、迁移或沉淀长期文档时，必须在同一轮改动中更新本文件；测试会检查每个 `docs/**/*.md` 是否出现在这里，避免正文有变更但没有入口。

## CLI 与同步说明

- [docs/cli-usage-for-llm.md](cli-usage-for-llm.md)：给 LLM 或自动化 agent 的完整 CLI 操作说明，覆盖接入、迁移、同步、可选模块和写入前校验。
- [docs/llm-usage-auto-config.md](llm-usage-auto-config.md)：用户授权 agent 自动判断接入方案时使用的精简协议。
- [docs/llm-usage-user-breakpoints.md](llm-usage-user-breakpoints.md)：需要用户选择 preset、模块或路径时使用的断点协议。
- [docs/llm-usage-user-breakpoints.json](llm-usage-user-breakpoints.json)：用户断点协议的机器可读结构，供 agent 直接解析选项和回复格式。

## 发布与运维

- [docs/release-process.md](release-process.md)：AgentPhilosophy CLI 和中央内容源的发版、版本口径、发布校验和依赖项目更新判断。

## 指南

- [docs/guides/aphilosophy-methodology.md](guides/aphilosophy-methodology.md)：维护或扩展 `aphilosophy/` 决策框架时使用的方法论和成果索引。
- [docs/guides/mattpocock-engineering-flow.md](guides/mattpocock-engineering-flow.md)：Matt Pocock 22 个活跃 skills 的完整能力集、`docs/agents/` 设置目录、AgentPhilosophy 托管边界和主线/分支用法。
- [docs/guides/value-specification-audit.md](guides/value-specification-audit.md)：面向开发者的价值规约审计指南，用于检查规则本身是否可信。

## 设计与计划

- [docs/plans/2026-05-10-agent-philosophy-design.md](plans/2026-05-10-agent-philosophy-design.md)：AgentPhilosophy 统一 Agent 规范管理系统的设计文档。
- [docs/superpowers/specs/2026-07-13-batch-sync-llm-documentation-design.md](superpowers/specs/2026-07-13-batch-sync-llm-documentation-design.md)：依赖项目批量同步版本后，按显式文档范围调用大模型更新项目自有文档的设计与安全边界。
- [docs/superpowers/specs/2026-07-13-flexible-multi-agent-and-optional-superpowers-design.md](superpowers/specs/2026-07-13-flexible-multi-agent-and-optional-superpowers-design.md)：灵活选择多 Agent 模型与推理强度，并将 Superpowers 调整为项目显式可选模块的设计。
- [docs/superpowers/plans/2026-07-13-flexible-multi-agent-and-optional-superpowers.md](superpowers/plans/2026-07-13-flexible-multi-agent-and-optional-superpowers.md)：按测试先行拆分多 Agent 规则、Superpowers 可选默认、LLM 合同和 0.7.7 本地 release 的实施步骤。
- [docs/superpowers/specs/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-design.md](superpowers/specs/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-design.md)：AgentPhilosophy 0.7.5 模板发布、默认 preset skill 刷新与 cadraq 无漂移同步设计。
- [docs/superpowers/plans/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-implementation.md](superpowers/plans/2026-07-10-agentphilosophy-0.7.5-cadraq-sync-implementation.md)：AgentPhilosophy 0.7.5 模板扩展、发布、cadraq 同步与验证执行计划。
