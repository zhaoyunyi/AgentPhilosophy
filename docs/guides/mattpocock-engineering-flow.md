# Matt Pocock 完整工程 Skill 家族

AgentPhilosophy 默认 preset 通过 `skill-mattpocock-engineering` 和独立的 `skill-improve-codebase-architecture`，提供 Matt Pocock 原生插件当前列出的 25 个活跃 skills。内容按 AgentPhilosophy 的中央源、双目标输出、项目目录、BDD/TDD 与 jj 合同做了适配；不引入上游 `deprecated`、`in-progress`、`misc` 和 `personal` 目录。

上游来源：https://github.com/mattpocock/skills

上游采用 MIT License。许可文本随主模块写入 `skills/MATTPOCOCK-SKILLS-LICENSE.txt` 与 `.agents/skills/MATTPOCOCK-SKILLS-LICENSE.txt`；可独立选择的 `code-review` 和 `improve-codebase-architecture` 模块也会在各自目录保留同一文本。

## 完整能力集

| 类别 | Skills |
| --- | --- |
| 路由与设置 | `ask-matt`、`setup-matt-pocock-skills` |
| 需求与规划 | `grill-me`、`grilling`、`grill-with-docs`、`to-spec`、`to-tickets`、`triage`、`wayfinder` |
| 实现与验证 | `implement`、`tdd`、`code-review`、`diagnosing-bugs`、`resolving-merge-conflicts` |
| 调研与设计 | `research`、`prototype`、`domain-modeling`、`codebase-design`、`improve-codebase-architecture` |
| 人工与沟通 | `wizard`、`to-questionnaire`、`wait-what` |
| 跨会话与学习 | `handoff`、`teach`、`writing-for-agents` |

`to-prd`、`to-issues` 与 `writing-great-skills` 是 AgentPhilosophy 为旧项目保留的兼容入口，不计入上游 25 个活跃 skills；新流程使用 `to-spec`、`to-tickets` 与 `writing-for-agents`。兼容入口不是 symlink 或失效占位符，而是仍会生成到两个 skill 根目录的真实 skill；其 `agents/openai.yaml` 禁止隐式调用，普通任务不会被旧名称抢占。

## “完整引入”的准确边界

本项目以 Matt 仓库 `.claude-plugin/plugin.json` 列出的 25 个活跃 skills 为完整性真值，并做三层保证：

1. 25 个活跃 skills 全部有项目级入口；`to-prd`、`to-issues`、`writing-great-skills` 另作为兼容入口保留。
2. 上游随 skill 使用的模板、脚本和说明文件按需一并带入，例如 `triage/AGENT-BRIEF.md`、`prototype/UI.md`、`diagnosing-bugs/scripts/hitl-loop.template.sh`；不是只复制一份 `SKILL.md`。
3. 每个目录同时写入 `skills/` 与 `.agents/skills/`，内容逐字节一致，并通过 `agents/openai.yaml` 声明展示信息和隐式触发策略。

“完整”不包含上游明确放在 `deprecated`、`in-progress`、`misc`、`personal` 下的非活跃内容，也不表示自动安装 GitHub/GitLab issue tracker、浏览器、测试框架或其他外部工具。需要外部系统的 skill 会正常被发现和读取，但真正执行仍取决于目标项目已有 CLI、MCP、登录态、权限与运行时依赖。

本地保留一个明确的行为适配：上游 `grilling` 已改为一次询问当前 frontier 的整轮问题；AgentPhilosophy 仍遵循项目约定的一问一答，每次只让用户拍板一个决策。其余 skill 不得把这项适配误写成已采用上游批量轮次。

## 推荐主线

```text
/ask-matt（不知道入口时）
-> /grill-with-docs
-> /to-spec
-> /to-tickets
-> 新开会话逐个 ticket 用 /implement
-> /tdd
-> /code-review
```

`to-spec`、`to-tickets` 与 `implement` 默认保持显式调用，避免所有项目无条件扩大隐式 skill 集。确实需要模型主动发现这三个核心阶段入口的项目，可以在 `.agentphilosophy.yaml` 中配置：

```yaml
vars:
  matt_implicit_skills:
    - to-spec
    - to-tickets
    - implement
```

当前只支持这三个值；未配置或使用空列表时继续生成 `allow_implicit_invocation: false`。`grill-*`、`triage`、`wayfinder`、`handoff` 和兼容入口仍保持各自既有调用策略，避免隐式改变工作阶段。

常见分支：

- 需要一手资料：`/research` 后回到 `/grill-with-docs`。
- 状态或界面问题无法靠讨论解决：`/handoff -> /prototype -> /handoff`。
- 疑难 bug：`/diagnosing-bugs`，修复后若发现缺少 seam，再进入 `/improve-codebase-architecture`。
- 超大且仍在迷雾中的工作：`/wayfinder`，地图收敛后回到 `/to-spec`。
- 外部 issue/PR 队列：`/triage`，形成 brief 后交给 `/implement`。
- 设计模块形状：`/codebase-design`；扫描候选由 `/improve-codebase-architecture` 完成。
- 冲突中的 jj/Git 操作：`/resolving-merge-conflicts`。
- 只能由人完成的控制台、凭据或切换：`/wizard`，生成交互脚本并保留人工 Gate。
- 答案掌握在外部知情人手中：`/to-questionnaire`，生成可异步填写的问卷。
- 上一句解释没有听懂：`/wait-what`，补足上下文后用简单语言重述。
- 编写 skill、`AGENTS.md`、`CLAUDE.md` 或被指向的 agent 文档：`/writing-for-agents`。

## 项目目录适配

首次使用 tracker、triage、wayfinder 或领域文档流程时运行 `/setup-matt-pocock-skills`。设置沿用上游更清晰的项目拥有目录：

```text
docs/agents/
├── issue-tracker.md
├── triage-labels.md
├── domain.md
└── out-of-scope/
```

同时保留 AgentPhilosophy 现有边界：

- `.agentphilosophy.yaml` 仍是模块、路径与同步配置真值。
- `AGENTS.md` / `CLAUDE.md` 是托管输出时，setup 写 `.agents/custom/AGENTS.custom.md`，再走 validate、dry-run、apply；不直接手改托管文件。
- 本地 spec 与 ticket 使用 `.scratch/<feature>/spec.md` 和 `.scratch/<feature>/issues/<NN>-<slug>.md`。
- 领域规范继续读取 `CONTEXT.md` / `CONTEXT-MAP.md`、`docs/adr/` 和 `spec/`。
- 新增 `docs/agents/` 长期文档时更新 `docs/README.md`。

没有必要创建 `.matt/` 或另一套隐藏配置/state 目录。

## 上下文与实现边界

`grill-with-docs`、`to-spec`、`to-tickets` 尽量在一个连续会话内完成。同一工具和目录中上下文接近上限时，在阶段边界 `/compact`；只有原型进入新目录/branch、切换工具或交给其他协作者时才 `/handoff`。每个 `/implement` 从 spec 与单票开始新会话。

`CONTEXT.md` 只存领域语言，ADR 只记录难反转且有真实权衡的决定，spec 描述行为与约束，ticket 必须是可独立验证的 vertical slice。实现使用最高稳定 seam 的行为测试，完成后按 Standards 与 Spec 双轴 review。

## 旧项目升级

旧项目模块列表显式冻结。只升级 AgentPhilosophy CLI 或依赖版本，不会静默修改 `.agentphilosophy.yaml`，也不会自动给旧项目追加 Matt、Portless、Reverse 或可选 Ponytail。升级后的行为分三种：

| 旧项目状态 | 升级后会发生什么 |
| --- | --- |
| 已包含 `skill-mattpocock-engineering` 与 `skill-improve-codebase-architecture` | `status` 会根据 state/version/hash 提示需要刷新；dry-run 展示文件计划，apply 才更新托管输出与 state |
| 只包含旧版 Matt 子集或只有其中一个模块 | 只刷新配置中已有模块；要完整家族必须显式补齐两个模块 |
| 完全未包含 Matt 模块 | 不产生 Matt skill 文件；需要先编辑模块列表，再走 validate、dry-run、apply |

需要完整家族时同时确认以下两个模块存在：

```yaml
modules:
  - existing-module
  - skill-improve-codebase-architecture
  - skill-mattpocock-engineering
```

然后执行：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

验证 repo 与 Codex 双目标：

```bash
find -L /path/to/project/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort
find -L /path/to/project/.agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort
```

每个 skill 的支持文件与 `agents/openai.yaml` 也应在两个目标目录逐字节一致；同名未托管文件存在时同步必须拒绝覆盖。

apply 成功后会发生这些可观察变化：

- 新增或刷新 25 个活跃 skill 入口，以及 `to-prd`、`to-issues`、`writing-great-skills` 三个兼容入口。
- `setup-matt-pocock-skills` 引导长期项目配置落在 `docs/agents/`，同时尊重 `.agentphilosophy.yaml` 和 `.agents/custom/` 的托管边界。
- `.agents/agentphilosophy-state.yaml` 记录新的 CLI/content version、模块版本和托管文件哈希；该文件由同步器维护，不手改。
- 同名且未被 AgentPhilosophy 托管的文件不会被直接覆盖；同步会先报告冲突，避免吞掉项目自有 skill。
- 已存在的 `deprecated`、个人 skill 或外部工具不会被 AgentPhilosophy 顺手删除；只有明确使用 `--prune-managed` 才处理已失活且仍保持原哈希的托管输出。
