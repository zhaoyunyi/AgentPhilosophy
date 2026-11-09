# 全部技能：选择、安装与使用

本页覆盖**当前 AgentPhilosophy 内容源能分发的全部技能**，不包括用户机器上其他插件或全局安装的技能。当前有 46 个不同技能名称、19 个安装模块；`code-review` 有两个互斥的提供模块，因此清单有 47 条技能与模块映射。以实际使用的内容源为准，旧固定 tag 不会包含后续新增内容。

## 先区分三个名称

| 对象 | 示例 | 用在哪里 |
| --- | --- | --- |
| 安装模块 | `skill-loop-check` | 追加到目标项目 `.agentphilosophy.yaml` 的 `modules` 列表 |
| 技能名称 | `loop-check` | 在 agent 会话中明确调用，例如 `$loop-check` |
| 同步命令 | `agentphilosophy-sync push` | 将已选择模块写入项目技能目录；它不执行巡检或其他技能任务 |

安装 CLI、启用项目模块、生成文件、宿主发现与实际执行是不同步骤。没有 `agentphilosophy-sync install-skill` 或 `run-skill` 命令，不要把技能名直接当成 shell 命令。

## 获取 CLI 和所需内容源

首次安装需要 Python 3.12+、uv 和仓库读取权限。下面使用已发布固定版本 `v1.2.1`；未来版本以正式 Release 和主 README 的稳定入口为准。这是复现用的固定版本示例，不代表后续未发布说明已在该 tag 中。

```bash
uv tool install git+https://github.com/zhaoyunyi/AgentPhilosophy.git@v1.2.1
agentphilosophy-sync --version
agentphilosophy-sync validate
```

已有安装要切换到指定版本时，用 `uv tool install --force` 指向相同的固定 tag 安装地址；完成后再次读取 `--version`。需要当前源码中的未发布更新时，在 AgentPhilosophy 根目录运行 `uv run --locked sync.py llm-usage`，或使用以下完整跨目录入口：

```bash
uv run --project /path/to/AgentPhilosophy /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy llm-usage
```

从 auto-config 或 user-breakpoints 切到本完整指南时，保留原命令的执行环境、工作目录、CLI/uv 前缀和 `--source`，只去掉 `--mode`/`--format`。例如 `agentphilosophy-sync --source /path/to/central-source llm-usage --mode user-breakpoints --format json` 应改为 `agentphilosophy-sync --source /path/to/central-source llm-usage`。JSON 的 `skill_guide.arguments` 供保留原前缀后调用；默认 `command` 不携带用户自定义来源。

`--source` 选择规范内容，不提供 Python 依赖环境；不要在普通业务仓库中假设存在 `sync.py`。安装版在非中央源目录运行时默认使用包内内容；从中央源目录调用会使用当前目录，所以应核对实际来源和版本。

## 安装到目标仓库

### 新项目

没有正式配置且没有需要接管的旧 Agent 文档时，先选择 `orchestrator`、`fullstack`、`frontend` 或 `mobile-sdk`：

```bash
agentphilosophy-sync validate
agentphilosophy-sync init /path/to/project --preset fullstack
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
agentphilosophy-sync status --project /path/to/project
```

`init` 只生成配置；`push --apply` 才生成技能。需要可选技能时，在 apply 前按下表修改 modules。已有 AGENTS/spec/skills 且没有正式配置的仓库先走 [迁移流程](migration.md)，不要用新项目流程强行覆盖。

### 已接入项目追加技能

1. 读取目标项目配置、现有技能、自有规则和 WIP，先确认表中安装模块是否已在 `modules` 中。即使 preset 后来增加技能，旧项目的显式 modules 列表也不会自动追加。
2. 从下表选模块并检查冲突/依赖，只追加缺少的项，保留原列表。比如启用巡检，只在现有 `modules` 列表末尾追加这一项：

```yaml
- skill-loop-check
```

以上是列表增量，不是完整配置；不要把 `existing-module` 等示意名写入真实配置，也不要运行 `init` 覆盖旧配置。选择整个 Matt 家族必须使用其模块，不能把 `grill-me`、`tdd` 等技能名称当成模块。

3. 使用同一内容源执行：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
agentphilosophy-sync status --project /path/to/project
```

dry-run 发现冲突时先按 [迁移与接管合同](migration.md) 处理；不要强行覆盖非托管技能或手改文件。已有明确授权继续沿用，只有新增范围或尚未解决的决策才提问。

### 输出目录与发现验证

默认生成 `skills/<技能名>/` 和 `.agents/skills/<技能名>/`，实际路径以 `skill_targets.repo_skills`、`skill_targets.codex_project` 为准。OpenSpec 的四个入口嵌套在 `<技能根>/openspec-skills/<技能名>/SKILL.md`。支持文件和 metadata 必须随模块一起同步，不仅复制 SKILL.md。

```bash
find /path/to/project/.agents/skills -name SKILL.md -print
find /path/to/project/skills -name SKILL.md -print
```

若改了目录，检查对应配置路径。需要 Claude 与 Codex 两路时，把 `repo_skills` 设为 `.claude/skills`；内置模块不会因设置 `claude_project` 自动生成第三路，也不会因省略 `codex_project` 关闭第二路。旧 `.codex/skills` 的保留与迁移见 [配置合同](configuration.md)。

文件和 state 验证通过后，在目标仓库打开新的 agent 会话，确认宿主列出相应技能，再执行下表的具体请求。宿主未列出时检查实际目录、同名冲突和当前内容源，必要时重新打开会话；不能以文件存在宣称已完成宿主发现验收。

## 哪些模块默认安装

下表的“默认”只描述**新建项目的 preset**；已有项目以自己的 modules 列表为准。

| 安装模块 | 新项目默认预设 | 额外条件 |
| --- | --- | --- |
| `openspec-skills` | 全部四类 | 四个 OpenSpec 技能；项目的 OpenSpec CLI/配置另行具备 |
| `skill-agentphilosophy-sync` | 全部四类 | 使用 AgentPhilosophy 同步器 |
| `skill-jj-management` | 全部四类 | 操作当前仓库的 jj |
| `skill-target-jj` | 全部四类 | 进入外部仓库前检查边界 |
| `skill-coding-standards` | 全部四类 | 读取目标仓库编码/测试规则 |
| `skill-repo-management` | 全部四类 | 文档、工作区、提交和清理规则 |
| `skill-loop-check` | 全部四类 | 生成自有巡检清单；不启动调度器 |
| `skill-restate-goal` | 仅 orchestrator | 其他类型需要时也可显式追加 |
| `skill-code-review-graph` | 全部四类 | CLI 随包安装；MCP 注册另行操作 |
| `skill-optimize-build-pipeline` | 全部四类 | 实际 CI/runner/registry 的访问与运行时另行具备 |
| `skill-orchestrate-grok-cli` | 全部四类 | 本机 Grok CLI、登录和授权另行具备 |
| `skill-reverse-skill` | 全部四类 | 仅在明确授权研究范围内使用；不安装逆向工具全集 |
| `skill-improve-codebase-architecture` | 全部四类 | 默认显式调用；生成评审报告后再选择实施方案 |
| `skill-mattpocock-engineering` | 全部四类 | 26 个本地技能，与独立架构评审合计覆盖 Matt 的 27 个活跃技能 |
| `skill-portless-local-dev` | 全部四类 | 技能可用不代表需要安装 Portless；按本地服务需求判断 |
| `skill-code-review` | 不默认 | 仅需审查入口时选；与 `skill-mattpocock-engineering` 互斥 |
| `skill-ponytail` | 不默认 | 精简编码判断；不安装上游插件或全局 hook |
| `skill-philosophy-extraction` | 不默认 | 必须同时启用 `aphilosophy` |
| `skill-ui-ux-loop` | 不默认 | 模块声明适用 frontend/fullstack；其他类型需按实际界面需求评估警告 |

`doc-templates`、各种 `spec-*`、`aphilosophy` 等模块输出规则/文档，不是需要逐个调用的技能。`superpowers-system` 也只输出项目说明，不安装 Superpowers 插件或其技能；只在明确点名时按 [Superpowers 合同](superpowers.md) 核对实际安装。

## 完整技能清单与请求示例

在 Codex 类支持 `$` 技能选择的宿主中使用下列请求；已有文档的 `/技能名` 是会话入口写法，具体选择方式以宿主实际技能列表为准。也可以明确说“使用技能 X，完成……”。这些都是发给 agent 的请求，不能粘贴到 shell 执行。

“自动”表示 metadata 允许在匹配任务时由模型选择，也可以明确点名；不表示保证每次被选择、常驻运行或获得额外权限。“显式”表示默认由用户点名。下面是默认策略，项目显式配置可改变三个 Matt 核心入口。

### 日常工程与项目维护

| 技能调用名 | 安装模块 | 默认调用 | 用途与产物 | 可复制请求示例 |
| --- | --- | --- | --- | --- |
| `$agentphilosophy-sync` | `skill-agentphilosophy-sync` | 自动 | 项目接入、同步与发现目录迁移，产出验证和状态结果 | 使用 $agentphilosophy-sync 给本仓追加已选模块并验证同步结果。 |
| `$jj-management` | `skill-jj-management` | 自动 | 当前仓库提交拆分、bookmark 与主线同步 | 使用 $jj-management 按功能拆分本轮改动并描述 change。 |
| `$target-jj` | `skill-target-jj` | 自动 | 进入外部仓库，先确认规则、WIP 和边界 | 使用 $target-jj 只读检查指定目标仓库能否开始修改。 |
| `$coding-standards` | `skill-coding-standards` | 自动 | 按项目编码规范实现并运行相关验证 | 使用 $coding-standards 修复这个已复现问题并记录测试结果。 |
| `$repo-management` | `skill-repo-management` | 自动 | 文档索引、工作区、提交边界与可追溯清理 | 使用 $repo-management 检查新增文档的入口和提交范围。 |
| `$loop-check` | `skill-loop-check` | 自动 | 按仓库清单查复用、一致性和退役等问题，修复、复查及 PR | 使用 $loop-check 检查本仓；在已有范围内修复并提交 PR。 |
| `$restate-goal` | `skill-restate-goal` | 自动 | 重述目标和待解决问题，标明不确定处 | 使用 $restate-goal 重述我当前的目标和要解决的问题。 |
| `$code-review-graph` | `skill-code-review-graph` | 自动 | 构建/查询结构图谱，定位调用方、影响范围与测试 | 使用 $code-review-graph 找出这个接口的调用方和相关测试。 |
| `$optimize-build-pipeline` | `skill-optimize-build-pipeline` | 自动 | 依据实测墙钟、CPU/I/O、缓存定位并优化流水线 | 使用 $optimize-build-pipeline 分析这次 CI 耗时并验证优化结果。 |
| `$orchestrate-grok-cli` | `skill-orchestrate-grok-cli` | 自动 | 编排隔离 Grok headless 任务，读取结束证据并独立审查 | 使用 $orchestrate-grok-cli 在已授权文件范围内完成这个任务。 |
| `$portless-local-dev` | `skill-portless-local-dev` | 自动 | 判断本地服务是否需要稳定命名 URL，产出最小接入方案 | 使用 $portless-local-dev 检查当前端口冲突并选择接入方式。 |
| `$reverse-skill` | `skill-reverse-skill` | 自动 | 按授权范围路由 APK/二进制/JS 等逆向与安全研究 | 使用 $reverse-skill 分析这个已授权本地样本，范围仅限附件。 |
| `$ponytail` | `skill-ponytail` | 自动 | 编码前评估复用与最小实现，避免无必要依赖和抽象 | 使用 $ponytail 评估这个需求能否复用现有能力。 |
| `$ui-ux-loop` | `skill-ui-ux-loop` | 自动 | 对实际界面做证据驱动审查、修复和复查 | 使用 $ui-ux-loop 检查这个页面的核心路径与移动布局。 |
| `$philosophy-extraction` | `skill-philosophy-extraction` | 自动 | 从文章提炼可执行决策框架及 aphilosophy 模板 | 使用 $philosophy-extraction 从这篇文章提取可验证的决策规则。 |

### OpenSpec

| 技能调用名 | 安装模块 | 默认调用 | 用途与产物 | 可复制请求示例 |
| --- | --- | --- | --- | --- |
| `$openspec-explore` | `openspec-skills` | 自动 | 只读探索现有 spec、实现和覆盖，说明差距 | 使用 $openspec-explore 检查这个 change 与当前实现的差距。 |
| `$openspec-propose` | `openspec-skills` | 自动 | 创建或审查 proposal、tasks 与设计约束 | 使用 $openspec-propose 为这个需求准备行为与验收规格。 |
| `$openspec-apply` | `openspec-skills` | 自动 | 实施已批准 change，逐项验证 | 使用 $openspec-apply 实现已确认的 change 并验证任务。 |
| `$openspec-archive` | `openspec-skills` | 自动 | 实现和验证完成后归档 change | 使用 $openspec-archive 归档这个已完成并验证的 change。 |

### Matt 工程流程

| 技能调用名 | 安装模块 | 默认调用 | 用途与产物 | 可复制请求示例 |
| --- | --- | --- | --- | --- |
| `$ask-matt` | `skill-mattpocock-engineering` | 显式 | 选择正确技能入口，不自行升级任务阶段 | 使用 $ask-matt 判断当前应先调研、澄清还是实现。 |
| `$setup-matt-pocock-skills` | `skill-mattpocock-engineering` | 显式 | 设置 tracker、triage 标签及领域资料入口 | 使用 $setup-matt-pocock-skills 接入本仓已有任务与领域文档。 |
| `$grill-me` | `skill-mattpocock-engineering` | 显式 | 一问一答压实需求，暂不修改长期文档 | 使用 $grill-me 逐步澄清这个想法的边界和验收条件。 |
| `$grill-with-docs` | `skill-mattpocock-engineering` | 显式 | 一问一答并同步 glossary/ADR 等长期决策 | 使用 $grill-with-docs 澄清方案并沉淀领域语言与决策。 |
| `$grilling` | `skill-mattpocock-engineering` | 自动 | 供访谈入口复用的一问一答流程 | 使用 $grilling 从风险最高的未知点开始逐问确认。 |
| `$domain-modeling` | `skill-mattpocock-engineering` | 自动 | 澄清实体、值对象、聚合与领域术语 | 使用 $domain-modeling 明确这几个业务概念的边界。 |
| `$to-spec` | `skill-mattpocock-engineering` | 显式（可配置） | 把已澄清上下文整理成规格，不重新访谈 | 使用 $to-spec 将已确认方案整理成规格与验收条件。 |
| `$to-tickets` | `skill-mattpocock-engineering` | 显式（可配置） | 将规格拆成独立可验证的纵向交付任务 | 使用 $to-tickets 将这份规格拆成有依赖顺序的 tickets。 |
| `$implement` | `skill-mattpocock-engineering` | 显式（可配置） | 实现一个规格/ticket，走 TDD 并完成 review | 使用 $implement 完成这个已确认 ticket 并运行验证。 |
| `$implement-spec` | `skill-mattpocock-engineering` | 显式 | 按依赖图编排整个规格，集成并统一验收 | 使用 $implement-spec 实现这份已拆票规格并汇总验收。 |
| `$tdd` | `skill-mattpocock-engineering` | 自动 | red-green-refactor，围绕可观察行为实现 | 使用 $tdd 先复现此行为缺陷，再做最小修复。 |
| `$code-review` | `skill-mattpocock-engineering` | 自动 | 按规范与规格两轴审查快照或改动 | 使用 $code-review 审查当前改动并给出有证据的 findings。 |
| `$triage` | `skill-mattpocock-engineering` | 显式 | 分类和核实外部 issue，形成可接手的 brief | 使用 $triage 梳理这个已选 issue 的事实、缺口与下一步。 |
| `$wayfinder` | `skill-mattpocock-engineering` | 显式 | 为跨会话的大任务建立共享决策地图 | 使用 $wayfinder 为这个路径尚不清晰的目标建立决策地图。 |
| `$research` | `skill-mattpocock-engineering` | 自动 | 用一手来源调研并写带引用的 Markdown 结论 | 使用 $research 调研这些方案并记录来源与适用条件。 |
| `$prototype` | `skill-mattpocock-engineering` | 自动 | 用可丢弃原型回答具体设计问题 | 使用 $prototype 验证这两种交互哪种能完成目标任务。 |
| `$diagnosing-bugs` | `skill-mattpocock-engineering` | 自动 | 建立证据、假设和复现，诊断疑难失败 | 使用 $diagnosing-bugs 定位这个偶发失败的根因。 |
| `$codebase-design` | `skill-mattpocock-engineering` | 自动 | 设计深模块、接口与可测试的边界 | 使用 $codebase-design 为已选重构设计接口和验证边界。 |
| `$pr` | `skill-mattpocock-engineering` | 自动 | 编写 PR 正文：问题、变化、证据及影响 | 使用 $pr 根据当前 diff 和测试结果编写 PR 正文。 |
| `$retro` | `skill-mattpocock-engineering` | 显式 | 复盘本轮 agent 导航、工具和工作环境 | 使用 $retro 找出这轮工作中值得修正的流程问题。 |
| `$handoff` | `skill-mattpocock-engineering` | 显式 | 生成供下一会话继续工作的交接文档 | 使用 $handoff 整理目标、已完成工作、证据与剩余阻塞。 |
| `$teach` | `skill-mattpocock-engineering` | 显式 | 按长期学习目标维护课程与进展 | 使用 $teach 围绕这个目标建立学习路径并开始第一课。 |
| `$to-questionnaire` | `skill-mattpocock-engineering` | 显式 | 把外部知识缺口整理成给知情人的问卷 | 使用 $to-questionnaire 将这些缺口整理成给接口负责人的问题。 |
| `$wait-what` | `skill-mattpocock-engineering` | 显式 | 补足上下文并用简单语言解释上一条消息 | 使用 $wait-what 用具体例子重新解释刚才的方案。 |
| `$wizard` | `skill-mattpocock-engineering` | 自动 | 为只能由人完成的操作生成人工可执行向导 | 使用 $wizard 将这些必须人工完成的控制台步骤做成向导。 |
| `$writing-for-agents` | `skill-mattpocock-engineering` | 自动 | 编写清晰可导航的 skill、规则与长期 agent 文档 | 使用 $writing-for-agents 改善这份 Agent 文档的入口和执行条件。 |
| `$improve-codebase-architecture` | `skill-improve-codebase-architecture` | 显式 | 识别架构摩擦并生成 HTML 重构候选报告 | 使用 $improve-codebase-architecture 审查本仓并给出重构候选。 |

### 只安装 code-review 的替代方案

| 技能调用名 | 安装模块 | 默认调用 | 用途与产物 | 可复制请求示例 |
| --- | --- | --- | --- | --- |
| `$code-review` | `skill-code-review` | 自动 | 不安装整个 Matt 家族时提供相同双轴审查入口 | 使用 $code-review 只读审查当前分支的规范和需求覆盖。 |

两种 `code-review` 提供方不能同时选择。默认 preset 已有 Matt 家族，无需再加独立模块。完整工程主线的推荐顺序是 `ask-matt` 路由 → 按需要 grill → `to-spec` → `to-tickets` → `implement` / `implement-spec` → `code-review`；只想核对目标时用 `restate-goal`，只想一次检查时无需走完整主线。

## 显式与自动调用如何配置

默认不为显式技能开启自动选择。需要改变 Matt 的三个核心入口时，在项目既有 `vars` 中合并配置：

```yaml
vars:
  matt_implicit_skills:
    - to-spec
    - to-tickets
    - implement
```

同步后重新核对两份 metadata 和宿主技能列表。这只改变上述三项，不会把 grill、setup、整份规格实现或复盘入口全部改成自动。其他技能按其实际 frontmatter 和 `agents/openai.yaml` 工作，不手改托管生成文件。

## 运行时与权限前提

| 能力 | 安装技能以外还需要什么 |
| --- | --- |
| OpenSpec | 目标项目已有 OpenSpec 命令、change/spec 和相关验证入口；技能文件不安装这些工具 |
| jj | 可用的 jj CLI 和项目版本控制规则；先检查安装与仓库状态 |
| code-review-graph | 包内固定 CLI 已包含；MCP 注册、hook 与用户级配置是单独操作，按 [图谱说明](code-review-graph.md) 执行 |
| Matt tracker、调研、原型与测试 | 对应 GitHub/GitLab CLI、浏览器/网络、项目运行时、测试命令和必要授权；`setup` 复用现有项目资料 |
| Portless | 按本地开发需求检查 Node/Portless，必要时安装；没有本地服务就不接入，见 [Portless](portless.md) |
| Grok 编排 | 已可用的 Grok CLI/登录、headless/hook 能力与限定写入范围，见 [Grok](grok-cli.md) |
| reverse-skill | 明确研究范围及实际分析工具，见 [逆向路由](reverse-skill.md)；不因技能可见而授权外部操作 |
| UI/UX Loop | 可检查的页面、启动入口或截图及交互目标；静态读源码不能证明真实界面体验通过 |
| Loop-Check | 项目专属清单和真实检查命令；每日执行还需用户要求启用后配置调度器，见 [Loop-Check](loop-check.md) |
| philosophy-extraction | 同时启用 `aphilosophy`；目标仓库边界与中央源维护权限分开 |

## 更新、卸载与排障

已接入项目的一句话升级、固定稳定版本、手动步骤和回退统一见 [升级指南](upgrade.md)。新流程从 1.3.0 开始提供，旧 CLI 先按正式发布版本完成一次安装引导。

- **安装包升级却没有新技能**：读取新版本的指南/模块，再把缺少的模块追加到项目配置并同步。`preset` 名称不替代已冻结的 modules。
- **文件存在但无法调用**：核对宿主列出的技能、发现目录、metadata 和同名项；重开目标仓库会话后再验证，不自动恢复全局 symlink。
- **validate 报 module missing**：所用内容源太旧或把技能名当成模块；先核对版本与上表，不自行发明模块 ID。
- **validate 报冲突/依赖缺失**：Matt 与独立 code-review 二选一；哲学提取补 `aphilosophy`。项目类型警告按真实用途判断。
- **想卸载**：从项目 modules 移除对应模块，先 dry-run，再 apply 刷新共享结果，成功后才对该单项目 `push /path/to/project --prune-managed`。手改文件冲突会保留；不删除项目自有计划。不要用 prune 代替更新或批量清理。
- **不知道选哪个**：先用本页用途与示例缩小范围；Matt 已安装时可调用 `$ask-matt`。实际输入中补上目标文件/change/页面、期望产物和授权范围。

维护者更新技能清单时，同时核对模块 `provides/outputs`、四类 preset、渲染后的 frontmatter 和 metadata。回归测试将完整 `llm-usage` 的清单与实际分发结果比较，避免新技能有文件却没有安装/调用说明。
