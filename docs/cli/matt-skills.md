## 十二、Matt Pocock 完整工程 skill 家族

当前中央源默认 preset 同时包含 `skill-mattpocock-engineering` 与 `skill-improve-codebase-architecture`。两者合计覆盖 Matt Pocock 原生插件当前声明的 27 个活跃 skills，并同步生成 repo skills、Codex 项目级 skills、支持文件和 `agents/openai.yaml`：

- 路由与设置：`ask-matt`、`setup-matt-pocock-skills`
- 需求与规划：`grill-me`、`grilling`、`grill-with-docs`、`to-spec`、`to-tickets`、`triage`、`wayfinder`
- 实现与验证：`implement`、`tdd`、`code-review`、`diagnosing-bugs`、`implement-spec`
- 调研与设计：`research`、`prototype`、`domain-modeling`、`codebase-design`、`improve-codebase-architecture`
- 人工与沟通：`wizard`、`to-questionnaire`、`wait-what`
- 跨会话与学习：`handoff`、`teach`、`writing-for-agents`、`retro`
- PR 表达：`pr`

推荐主线：

```text
/grill-with-docs
-> /to-spec
-> /to-tickets
-> 逐票 /implement，或整份 spec 用 /implement-spec
```

`to-spec`、`to-tickets` 与 `implement` 默认保持显式调用。需要让模型主动发现这三个核心阶段入口的项目，可在 `.agentphilosophy.yaml` 的 `vars` 中按需配置：

```yaml
vars:
  matt_implicit_skills:
    - to-spec
    - to-tickets
    - implement
```

当前只支持上述三个值；默认空列表不会改变其他项目的调用策略。重流程入口、设置入口、会改变工作阶段的其他 skill 不应因本配置自动转为隐式调用。

使用含义：

- `/ask-matt`：不知道正确入口时只做 skill 路由。
- `/setup-matt-pocock-skills`：配置 `docs/agents/` 下的 tracker、triage 与领域文档合同；AgentPhilosophy 项目通过 `.agents/custom/AGENTS.custom.md` 接入托管入口。
- `/grill-me`：只做一问一答的无文档拷问；需要同步沉淀领域语言和决策时改用 `/grill-with-docs`。
- `/grill-with-docs`：先拷问计划、决策或想法，同时沉淀 `GLOSSARY.md`、ADR 和领域语言。
- `/to-spec`：把已经讨论清楚的内容整理成 spec，不重新访谈。
- `/to-tickets`：把 spec 拆成独立、可验证的 tracer-bullet vertical slice ticket；本地模式按 `.scratch/<feature-slug>/issues/<NN>-<slug>.md` 一票一文件保存。
- `/implement`：按单个 spec/ticket 实现，内部走 `/tdd`，最后跑 `/code-review`。
- `/implement-spec`：按阻塞依赖图编排完整 spec，独立 workspace 实现、单一 owner 集成，最后统一 review。

- `/triage`、`/wayfinder`：分别处理外部需求队列与超过单会话的决策地图。
- `/research`、`/prototype`、`/diagnosing-bugs`：分别提供一手资料、可丢弃验证和证据化诊断分支。
- `/codebase-design` 与 `/improve-codebase-architecture`：前者设计深模块 Interface/seam，后者扫描候选并生成报告。
- `/pr`：用改动、前后证据和合入影响组织 PR 正文。
- `/retro`：复盘会话的导航、自动检查、指令与工具。
- `/wizard`：把必须由人完成的控制台、凭据、迁移或切换步骤固化成可验证的交互脚本；agent 能自行完成时不使用。
- `/to-questionnaire`：把用户缺少的外部知识整理成给特定知情人的 Markdown 问卷。
- `/wait-what`：补足上下文并用更简单的语言重述上一条消息。
- `/handoff`、`/teach`、`/writing-for-agents`：处理跨会话交接、状态化教学和面向 agent 的文档设计。

更多最佳实践见 [docs/guides/mattpocock-engineering-flow.md](../guides/mattpocock-engineering-flow.md)。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动向旧配置追加新模块。需要让旧项目拿到完整家族时，确认两个模块都在现有 `modules` 中，不要替换已有模块：

```yaml
modules:
  - existing-module
  - skill-improve-codebase-architecture
  - skill-mattpocock-engineering
```

随后执行标准同步流程：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
agentphilosophy-sync push /path/to/project --prune-managed
```

清理前先确认新输出完整且旧托管文件没有手改；`--prune-managed` 只处理 state 登记且哈希未变的失活文件，发现手改时报告冲突并保留内容。

同步后验证：

```bash
find -L /path/to/project/.agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort
find -L /path/to/project/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort
```

每个 skill 的两个目标目录应逐字节一致。同名未托管文件存在时，`push --apply` 必须拒绝覆盖。`setup-matt-pocock-skills` 沿用上游 `docs/agents/` 目录，同时保持 `.agentphilosophy.yaml` 为同步配置真值、`.agents/custom` 为托管入口扩展源、本地 ticket 位于 `.scratch/`；不创建第二套隐藏配置目录。

这里的“完整”以 Matt 上游插件 manifest 的 27 个活跃 skills 为边界，不引入 `deprecated`、`in-progress`、`misc`、`personal` 或尚未毕业的 beta skill。skill 文件、支持文件、双根输出和触发元数据完整可用；需要 GitHub/GitLab tracker、浏览器、测试框架或其他外部系统的动作，仍取决于目标项目已经提供相应 CLI/MCP、登录态、权限和运行时，AgentPhilosophy 不会凭 skill 文件自动安装凭据或外部工具。

上游 `grilling` 当前使用 frontier 批量轮次；AgentPhilosophy 按项目协作约定保留一问一答，每轮只让用户确认一个决策。这是有意适配，不是遗漏；生成到目标项目的 `grill-me`、`grill-with-docs`、`grilling` 与 `triage` 应保持同一口径。
