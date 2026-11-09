# AgentPhilosophy 统一 Agent 规范管理系统 - 修正版设计文档

> 日期：2026-05-10
> 状态：审查后修订
> 修订依据：已核对 ExampleFullstackProject、ExampleOrchestratorProject、ExampleFrontendProject、ExampleMobileSDKProject 的根级入口、`spec/`、`docs/guides|guide/`、项目级 skills 布局。

## 一、项目定位

AgentPhilosophy 是一个**中央规范管理仓库**，统一管理跨项目共享的 Agent 协作规范、Spec 工程规范、Skill 集合库。通过模板渲染、托管状态记录和同步脚本，实现：

- 一处修改，多项目可控同步更新。
- 每个项目保留自定义扩展空间。
- 新项目快速接入，老项目安全迁移。
- 通用模块可复用，项目特有规则不被覆盖。

## 二、核心设计决策

| 决策项 | 修正版选择 | 理由 |
|--------|------------|------|
| 架构模式 | 分层架构 + 同步脚本 | 兼顾中央更新和项目定制 |
| 模块粒度 | 按功能独立，项目按需组合 | 扩展性最高 |
| 渲染引擎 | Python + Jinja2 | 稳定成熟，适合 Markdown 条件和循环 |
| 输出行为 | 以 `outputs[]` 为准 | 避免模块级 `mode` 和输出类型冲突 |
| 定制方式 | yaml 配置 + custom 文件 + managed state | 结构化配置管路径/变量，长内容放 custom，状态文件保证安全更新 |
| Spec 定制 | 混合模式 | 通用原则可托管，项目落地约束必须可扩展 |
| Skill 安装 | target 抽象 | 同时支持 `.claude/skills/`、仓库 `skills/` 和 Codex 原生 `.codex/skills/` |
| 老项目迁移 | report-first | 第一版只生成报告和草稿，不自动覆盖现有有效规则 |
| 新项目接入 | 轻量 preset | 用声明式默认模块和路径提升 init 速度，不引入复杂生成器 |
| 老项目接管 | adopt 流程 | 用户确认后只登记 hash，不改内容，后续才能安全托管更新 |

## 三、项目目录结构

```text
AgentPhilosophy/
├── modules/
│   ├── openspec-skills/
│   ├── jj-conventions/
│   ├── model-constraints/
│   ├── doc-templates/
│   ├── multi-module-layout/
│   ├── deploy-conventions/
│   │
│   ├── spec-program/
│   ├── spec-ddd/
│   ├── spec-bdd/
│   ├── spec-test-browser/
│   ├── spec-test-mobile/
│   ├── spec-test-general/
│   ├── spec-ui/
│   ├── spec-architecture/
│   ├── spec-ios-sdk/
│   ├── spec-feature-domain/
│   │
│   ├── skill-jj-management/
│   ├── skill-target-jj/
│   ├── skill-coding-standards/
│   └── skill-repo-management/
│
├── presets/
│   ├── orchestrator.yaml
│   ├── fullstack.yaml
│   ├── frontend.yaml
│   └── mobile-sdk.yaml
├── catalog.yaml
├── templates/
│   └── managed-file-header.md.j2
├── registry.example.yaml
├── registry.yaml        # local, ignored
├── sync.py
├── pyproject.toml
├── README.md
└── docs/
    ├── cli-usage-for-llm.md
    └── plans/
```

`registry.yaml` 是本机真实批量目标入口；`push --all` 和不带 `--project` 的 `status` 都从该文件读取项目列表。该文件可以包含本机绝对路径，已加入 `.gitignore`，不作为跨机器模板使用。`registry.example.yaml` 是可复用模板，用于复制成新的本机 `registry.yaml` 后再改路径。

### 3.1 模块分层

基础模块：

- `openspec-skills`：OpenSpec propose/apply/explore/archive 四件套。
- `jj-conventions`：jj colocated git、bookmark、中文 change 描述、提交拆分规则。
- `model-constraints`：多 Agent 模型和 reasoning 继承约束。
- `doc-templates`：`AGENTS.md`、`CLAUDE.md`、AI 协作文档骨架。
- `multi-module-layout`：子目录入口、跨仓只读搜索、目录边界。
- `deploy-conventions`：本地、QA、远端部署索引规则。

Spec 模块：

- `spec-program`：开发总原则，默认 layered。
- `spec-ddd`：DDD 原则，默认 managed_replace，但老项目首次接入必须 report-first。
- `spec-bdd`：BDD 输出和验收规范。
- `spec-test-browser`：Playwright / Browser Use 选择规范。
- `spec-test-mobile`：iOS / Android / 真机 / 模拟器测试策略。
- `spec-test-general`：项目测试分层，如 ExampleFrontendProject 的 `TestStrategy.md`。
- `spec-ui`：UI / 设计系统规范，默认 layered。
- `spec-architecture`：项目架构约束，如 ExampleFrontendProject 的 `ArchitectureSpec.md`。
- `spec-ios-sdk`：ExampleMobileSDKProject 的 `iOSSDK*.md` 系列规范，作为 mobile-sdk preset 可选模块。
- `spec-feature-domain`：ExampleMobileSDKProject 的 `spec/features/*` 领域功能规范，默认 init_only 或 layered。

Skill 模块：

- `skill-jj-management`：当前仓库 jj 操作。
- `skill-target-jj`：进入外部 jj 仓库时的目标仓库操作。
- `skill-coding-standards`：编码、审查、测试入口。
- `skill-repo-management`：仓库状态、文档索引、提交边界、清理规则。

### 3.2 Preset 目录

Preset 是轻量声明，不是复杂生成器。它只提供默认模块、默认路径、默认 skill targets 和推荐变量，项目仍可在 `.agentphilosophy.yaml` 中覆盖。

第一版内置：

- `orchestrator`：适合 ExampleOrchestratorProject 这类编排器项目。
- `fullstack`：适合 ExampleFullstackProject 这类前后端 + 部署 + OpenSpec 项目。
- `frontend`：适合 ExampleFrontendProject 这类前端主导项目。
- `mobile-sdk`：适合 ExampleMobileSDKProject 这类移动 SDK / 多子工程工作区。

示例：

```yaml
# presets/mobile-sdk.yaml
name: mobile-sdk
description: 移动端 SDK / 多子工程工作区默认接入方案
modules:
  - openspec-skills
  - jj-conventions
  - model-constraints
  - doc-templates
  - multi-module-layout
  - spec-program
  - spec-ddd
  - spec-bdd
  - spec-test-browser
  - spec-test-mobile
  - spec-ui
  - spec-ios-sdk
  - spec-feature-domain
  - skill-jj-management
  - skill-target-jj
paths:
  docs_guide_dir: docs/guide
  spec_dir: spec
skill_targets:
  repo_skills: skills
  codex_project: .codex/skills
  claude_project: .claude/skills
```

`init --preset mobile-sdk` 使用 preset 生成配置草稿；`push` 只读取项目 `.agentphilosophy.yaml`，不隐式读取 preset，避免 preset 更新自动改变老项目行为。

### 3.3 模块目录索引

`catalog.yaml` 是给人和工具共同使用的模块索引。它不替代 `module.yaml`，只提供全局检索、分类和风险说明。

```yaml
schema_version: 1
modules:
  - name: spec-ios-sdk
    category: spec
    description: iOS SDK API、架构、组件、交互和包边界规范
    project_types: [mobile-sdk]
    outputs:
      - spec/iOSSDKAPISpec.md
      - spec/iOSSDKArchitectureSpec.md
    risk: medium
    notes: 老项目默认 report_only，避免覆盖已有 SDK 交付规范。
```

`validate` 命令会检查 `catalog.yaml` 中声明的模块是否真实存在，并提示未登记的新模块。

## 四、模块定义规范

每个模块必须有 `module.yaml`。模块级字段只定义元信息、默认变量和默认策略；实际写文件行为必须由 `outputs[]` 明确声明。

```yaml
name: spec-ddd
description: DDD 领域驱动设计规范
version: 1.0.0

default_strategy: managed_replace

project_types:
  - orchestrator
  - fullstack
  - frontend
  - mobile-sdk

requires: []
conflicts: []

provides:
  - spec:ddd

default_vars:
  aggregate_style: "事件溯源"

outputs:
  - id: ddd-spec
    type: rendered_file
    template: templates/DDDSpec.md.j2
    target: "{{ paths.spec_dir }}/DDDSpec.md"
    strategy: managed_replace
    on_existing_unmanaged: report_only

  - id: ddd-agents-fragment
    type: fragment
    template: templates/ddd-rules.md.j2
    target: AGENTS.md
    section: ddd_conventions
    order: 20

  - id: openspec-propose-skill
    type: copy_tree
    source: files/openspec-propose/
    target: "{{ skill_targets.claude_project }}/openspec-propose/"
    strategy: managed_replace
```

### 4.1 输出类型

| type | 行为 | 适用场景 |
|------|------|----------|
| `rendered_file` | Jinja2 渲染单文件 | spec、AGENTS/CLAUDE base、skill 模板 |
| `fragment` | 渲染片段，交给目标主模板按 section 拼接 | model、jj、deploy 等规则片段 |
| `copy_file` | 复制单文件 | 固定脚本、静态模板 |
| `copy_tree` | 复制目录树 | OpenSpec skills |

### 4.2 写入策略

| strategy | 行为 | 默认安全性 |
|----------|------|------------|
| `managed_replace` | 只替换已由 AgentPhilosophy 托管且 hash 匹配的目标文件 | 安全 |
| `layered` | 渲染 base，拼接 custom，输出最终文件 | 安全 |
| `init_only` | 目标不存在时创建；存在则跳过 | 最安全 |
| `report_only` | 只生成候选内容和 diff，不写目标文件 | 迁移默认 |

### 4.3 未托管文件处理

`on_existing_unmanaged` 可选值：

- `fail`：发现目标文件存在但不在 managed state 中，直接失败。
- `warn`：打印警告，跳过该文件。
- `report_only`：生成报告和候选文件，不写目标文件。

老项目 migrate 和首次 push 默认使用 `report_only`，避免覆盖已有有效规则。

### 4.4 依赖、冲突和适用项目

模块可以声明依赖、冲突、适用项目类型和能力标识：

```yaml
requires:
  - doc-templates
conflicts:
  - legacy-agent-docs
project_types:
  - fullstack
  - orchestrator
provides:
  - docs:agents
  - skill:jj-management
```

校验规则：

- 启用模块的 `requires` 必须全部在最终模块集合中。
- `conflicts` 命中的模块不能同时启用。
- `project_types` 不匹配时给警告，不强制失败；用户可通过 `allow_project_type_mismatch: true` 显式接受。
- `provides` 用于报告能力覆盖和后续冲突诊断，不参与写入决策。

## 五、目标项目配置

目标项目通过 `.agentphilosophy.yaml` 声明路径、模块、变量和安装目标。

```yaml
project_name: ExampleOrchestratorProject
project_type: orchestrator
preset: orchestrator
description: Python 编排器，调度 Claude Code 和 Codex CLI 子 agent

paths:
  agent_work_dir: .agents
  spec_dir: spec
  docs_guide_dir: docs/guides
  custom_dir: .agents/custom
  generated_dir: .agents/generated
  migration_dir: .agents/migration

skill_targets:
  claude_project: .claude/skills
  repo_skills: skills
  codex_project: .codex/skills

modules:
  - openspec-skills
  - jj-conventions
  - model-constraints
  - doc-templates
  - multi-module-layout
  - spec-program
  - spec-ddd
  - spec-bdd
  - spec-test-browser
  - spec-ui
  - skill-jj-management
  - skill-target-jj
  - skill-coding-standards

allow_project_type_mismatch: false

vars:
  language: python
  test_command: "pytest -q"
  primary_tool: "Codex CLI"
  jj_workspace_dir: ".example-project-workspaces/"
  extra_model_rules:
    - "禁止使用 gpt-5.2/gpt-5.3-codex"
  sub_directories:
    - name: core
      description: 核心模块（任务加载、步骤执行、上下文管理）
    - name: skills
      description: 项目级 skills
```

`synced_versions` 和 `last_synced` 不再写入 `.agentphilosophy.yaml`，避免工具运行频繁改动用户配置。同步状态统一记录到 `.agents/agentphilosophy-state.yaml`。

`preset` 只记录项目初始化时采用的默认方案，便于审计和后续人工比较。同步时不自动重新展开 preset；如果需要更新项目模块，必须显式修改 `.agentphilosophy.yaml`。

中央源路径不写入目标项目配置；CLI 从当前工作目录推断中央源，或通过全局参数 `--source /path/to/AgentPhilosophy` 显式指定。

### 5.1 路径差异

不同项目的文档目录不同，必须通过 `paths` 配置适配：

- ExampleFullstackProject、ExampleOrchestratorProject、ExampleFrontendProject：默认 `docs/guides`。
- ExampleMobileSDKProject：使用 `docs/guide`。
- Spec 默认目录为 `spec`，但仍保留配置项，便于未来项目调整。

## 六、目标项目文件布局

sync 后目标项目可能新增：

```text
目标项目/
├── .agentphilosophy.yaml
├── .agents/
│   ├── agentphilosophy-state.yaml
│   ├── generated/
│   │   ├── AGENTS.base.md
│   │   ├── CLAUDE.base.md
│   │   └── spec/
│   ├── custom/
│   │   ├── AGENTS.custom.md
│   │   ├── CLAUDE.custom.md
│   │   └── ProgramSpec.custom.md
│   └── migration/
│       ├── inventory.md
│       ├── proposed.agentphilosophy.yaml
│       └── diffs/
├── AGENTS.md
├── CLAUDE.md
├── spec/
├── .claude/skills/
└── skills/
```

### 6.1 Managed state

`.agents/agentphilosophy-state.yaml` 记录所有被工具托管的输出：

```yaml
schema_version: 1
source: central-source
source_revision: jj:unknown-or-git-sha
source_tree_hash: sha256:...
last_synced: 2026-05-10T21:40:00+08:00

modules:
  spec-ddd: 1.0.0
  model-constraints: 1.1.0

files:
  - path: spec/DDDSpec.md
    module: spec-ddd
    output_id: ddd-spec
    strategy: managed_replace
    source_hash: sha256:...
    rendered_hash: sha256:...
    last_written_hash: sha256:...
```

写入前必须检查：

1. 目标文件不存在：可以创建。
2. 目标文件存在且在 state 中：只有当前 hash 等于 `last_written_hash` 才能覆盖。
3. 目标文件存在但不在 state 中：按 `on_existing_unmanaged` 处理。
4. 目标文件在 state 中但用户手动改过：停止覆盖，生成冲突报告。

`source_revision` 优先记录 AgentPhilosophy 自身的 jj change id；如果不是 jj 仓库则记录 git commit；如果两者都不存在则写 `none` 并保留 `source_tree_hash`。`source_tree_hash` 对 `modules/`、`presets/`、`templates/`、`catalog.yaml` 计算，便于未来排查某个项目到底来自哪一版中央源。

## 七、模板渲染与组合机制

`doc-templates` 提供主骨架，其他模块提供 fragment。Jinja2 不使用自定义 tag，统一注入 `section(name)` 函数：

```jinja2
{# modules/doc-templates/templates/AGENTS.md.j2 #}
# {{ project_name }} Agent 协作规范

> {{ description }}

## 通用约定

{{ section("model_constraints") }}
{{ section("version_control") }}
{{ section("module_boundary") }}
{{ section("deploy") }}
{{ section("ddd_conventions") }}
```

组合流程：

1. 收集所有启用模块的 `fragment` 输出。
2. 按 `target + section + order` 排序。
3. 渲染主骨架时通过 `section(name)` 注入片段内容。
4. `layered` 输出先生成 base，再拼接对应 custom。
5. 空 section 不输出内容，避免空标题。

变量优先级：

```text
内置变量 paths/skill_targets/modules
  < 模块 default_vars
  < 项目 vars
  < 命令行 --var 临时覆盖
```

## 八、sync.py 命令接口

```bash
# 推模式；不带 --apply 时只输出计划，不写目标文件
uv run sync.py push /path/to/target-project --dry-run
uv run sync.py push /path/to/target-project --apply

# 初始化新项目配置
uv run sync.py init /path/to/new-project --preset mobile-sdk
uv run sync.py init /path/to/new-project --interactive

# 老项目迁移分析，默认不写正式目标文件
uv run sync.py migrate /path/to/existing-project

# 如果 migrate --help 已暴露 --write-config：只在正式配置不存在时从迁移草稿写入
uv run sync.py migrate /path/to/existing-project --write-config

# 校验中央仓库或目标项目配置，不写文件
uv run sync.py validate
uv run sync.py validate /path/to/project

# 接管已确认的老项目文件：不改内容，只登记当前 hash 到 state
uv run sync.py adopt /path/to/project --file AGENTS.md --module doc-templates --output agents-md
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml

# 批量推送本机 registry.yaml 中的项目
uv run sync.py push --all

# 只看变更，不写文件
uv run sync.py push /path/to/project --dry-run

# 查看状态
uv run sync.py status --project /path/to/project

# 清理 state 中确认由本工具托管且已从当前配置移除的文件
uv run sync.py push /path/to/project --prune-managed

# 占位命令；第一版只返回 warning
uv run sync.py pull
```

执行流程：

1. 读取 `.agentphilosophy.yaml`。
2. 合并默认路径、skill targets 和 vars。
3. 校验模块存在、依赖满足、冲突不存在、输出 id 唯一、目标路径未越界。
4. 渲染所有 fragment。
5. 渲染或复制每个 output。
6. 根据 state/hash 判断能否写入。
7. 写入文件和新的 state。
8. 输出变更摘要、跳过原因和冲突报告路径。

## 九、安全机制

硬规则：

- 默认不覆盖未托管的既有文件。
- `custom/` 目录永不覆盖。
- `migrate` 第一版只生成报告和草稿，不直接改正式目标文件。
- `--dry-run` 必须展示将新增、更新、跳过、冲突的文件列表。
- `--prune-managed` 只删除 state 中登记、当前 hash 仍匹配、且已从当前配置输出中移除的托管文件；它必须要求明确的单个目标项目路径，不和 `--dry-run`、`--apply` 或 `--all` 混用。删除文件后只尝试清理该文件的直接空目录。
- 如果 `migrate --write-config` 存在，只能在目标项目根目录 `.agentphilosophy.yaml` 不存在时，把 `.agents/migration/proposed.agentphilosophy.yaml` 写入正式配置；正式配置已存在时必须拒绝覆盖。
- 任何目标路径必须限制在目标项目目录内，禁止 `../` 越界写入。
- `adopt` 不修改目标文件内容，只把用户确认接管的当前文件 hash 写入 state。

冲突输出示例：

```text
[conflict] spec/DDDSpec.md
  reason: file exists but is not managed by AgentPhilosophy
  action: wrote candidate to .agents/migration/diffs/spec-DDDSpec.md.new
```

## 十、Init 与 Migrate 工作流

### 10.1 新项目 init

`init` 当前只负责生成项目根目录 `.agentphilosophy.yaml`，不渲染托管输出，也不会自动执行 `push --dry-run`。新项目推荐传入 `--preset`，减少重复配置；需要人工输入项目名、类型、描述和测试命令时可使用 `--interactive`。

```bash
uv run sync.py init /path/to/new-mobile-sdk --preset mobile-sdk
uv run sync.py init /path/to/new-fullstack --interactive
uv run sync.py validate /path/to/new-mobile-sdk
uv run sync.py push /path/to/new-mobile-sdk --dry-run
uv run sync.py push /path/to/new-mobile-sdk --apply
```

### 10.2 老项目 migrate

第一版 migrate 目标是“安全盘点”，不是自动改造：

1. 扫描 `AGENTS.md`、`CLAUDE.md`、`spec/`、`.claude/skills/`、`skills/`、`docs/guides|guide/`。
2. 生成模块候选清单。
3. 生成 `.agents/migration/proposed.agentphilosophy.yaml`，但不自动提升为正式 `.agentphilosophy.yaml`。
4. 生成现有文件和候选输出的 diff。
5. 标注哪些内容建议进入 custom，哪些内容建议保持项目自维护。
6. 生成可选的 `.agents/migration/adopt-plan.yaml`，列出建议接管的文件和建议保持自维护的文件。
7. 不自动拆分原文件，不自动覆盖正式目标。

```bash
uv run sync.py migrate /path/to/ExampleOrchestratorProject
```

`push` 只读取项目根目录 `.agentphilosophy.yaml`。老项目完成 `migrate` 后，必须先人工确认并落地正式 `.agentphilosophy.yaml`，再运行 `adopt`、`validate`、`push --dry-run` 和 `push --apply`。

如果当前 CLI 提供 `migrate --write-config`，它只是“从迁移草稿写入正式配置”的安全捷径：

- 先生成 `.agents/migration/proposed.agentphilosophy.yaml`。
- 仅当项目根目录 `.agentphilosophy.yaml` 不存在时写入正式配置。
- 如果正式配置已经存在，必须报错拒绝覆盖。
- 不自动接管文件，不写托管输出，不跳过后续 `validate`、`adopt` 和 `push --dry-run`。

### 10.3 老项目 adopt

`adopt` 用于用户确认迁移报告后接管既有文件。它不改变文件内容，只登记当前 hash，让后续 `managed_replace` 有安全基线。

```bash
# 单文件接管
uv run sync.py adopt /path/to/ExampleOrchestratorProject --file AGENTS.md --module doc-templates --output agents-md

# 按 migrate 生成的接管计划批量登记
uv run sync.py adopt /path/to/ExampleOrchestratorProject --from-report .agents/migration/adopt-plan.yaml
```

adopt 必须满足：

- 目标文件存在。
- 文件路径没有越界。
- 对应 `module/output_id` 存在。
- 如果文件已在 state 中，当前 hash 必须等于 state 记录，否则拒绝覆盖登记。
- adopt 后在正式 `.agentphilosophy.yaml` 就绪的前提下立刻运行 `push --dry-run`，确认候选更新不会意外覆盖项目特定内容。

## 十一、版本管理与状态追踪

`registry.yaml` 保留本机真实批量目标：

```yaml
projects:
  - name: ExampleFullstackProject
    path: /path/to/ExampleFullstackProject
  - name: ExampleOrchestratorProject
    path: /path/to/ExampleOrchestratorProject
  - name: ExampleFrontendProject
    path: /path/to/ExampleFrontendProject
  - name: ExampleMobileSDKProject
    path: /path/to/ExampleMobileSDKProject
```

`registry.example.yaml` 提供可复用模板，不参与真实批量同步。新机器应先复制模板为 `registry.yaml`，再写入本机真实项目路径；`registry.yaml` 属于本机配置，默认不提交。

批量同步要求目标项目已经存在正式 `.agentphilosophy.yaml`；未接入项目先通过 `init` 或 `migrate` 接入。

`status --project /path/to/project` 对比：

- 目标项目是否存在 `.agentphilosophy.yaml`。
- state 中模块版本是否落后于中央 modules。
- state 中 `source_revision` / `source_tree_hash` 是否落后于当前中央源。
- state 中托管文件是否被用户手动改动。
- 是否存在已废弃但仍可安全 prune 的托管文件。

不带 `--project` 的 `status` 检查 `registry.yaml` 中的项目路径；如果自定义中央源未提供 registry，会返回 warning。

## 十二、Validate 规则

`validate` 分两类：

```bash
# 校验 AgentPhilosophy 中央源
uv run sync.py validate

# 校验某个目标项目配置和可渲染性
uv run sync.py validate /path/to/project
```

中央源校验：

- `modules/*/module.yaml` 必须存在且 YAML 合法。
- `outputs[].id` 在同一模块内唯一。
- `outputs[].type`、`strategy`、`on_existing_unmanaged` 必须是已知值。
- `requires` 指向的模块必须存在。
- `conflicts` 指向的模块若不存在，给 warning。
- `catalog.yaml` 中的模块必须存在；存在但未登记的模块给 warning。
- `presets/*.yaml` 引用的模块必须存在。
- 模板文件路径必须存在。

目标项目校验：

- `.agentphilosophy.yaml` YAML 合法。
- `preset` 若存在，必须能在 `presets/` 中找到。
- 项目启用模块存在、依赖满足、无冲突。
- `paths`、`skill_targets` 展开后不得越界。
- 所有模板可以在 strict undefined 模式下渲染。
- 输出目标不能互相覆盖，除非显式声明相同 target 的 fragment 组合。

## 十三、Skill 库规则

Skill 模块不得假设唯一安装位置。每个 skill output 必须声明目标：

```yaml
outputs:
  - id: jj-management-repo-skill
    type: rendered_file
    template: templates/SKILL.md.j2
    target: "{{ skill_targets.repo_skills }}/{{ project_slug }}-jj-management/SKILL.md"
    strategy: managed_replace

  - id: jj-management-claude-skill
    type: rendered_file
    template: templates/SKILL.md.j2
    target: "{{ skill_targets.claude_project }}/jj-management/SKILL.md"
    strategy: managed_replace
```

项目强相关 skill 优先输出到仓库 `skills/`；Claude Code 专用 skill 输出到 `.claude/skills/`；Codex 原生项目级 skill 输出到 `.codex/skills/`，由 `skill_targets.codex_project` 控制。

## 十四、扩展新模块的流程

添加新模块：

1. 在 `modules/` 下创建模块目录。
2. 编写 `module.yaml`，确保每个 `outputs[].id` 唯一，并声明 `requires` / `conflicts` / `project_types`。
3. 编写模板或复制源文件。
4. 更新 `catalog.yaml`。
5. 如适合新项目快速接入，更新对应 `presets/*.yaml`。
6. 运行 `uv run sync.py validate`。
7. 本地用临时目标目录跑 `sync.py push --dry-run`。
8. 加入某个真实项目前先跑 `migrate` 或 `push --dry-run`。
9. 确认无未托管覆盖后再 `--apply`。

## 十五、第一版实现范围

第一版只实现安全核心，不追求自动迁移智能化：

必须实现：

- `push`、`status`、`migrate`、`init`、`validate`、`adopt` 命令骨架，以及 `pull` 占位提示。
- Jinja2 渲染和 `section(name)` 注入。
- `rendered_file`、`fragment`、`copy_tree`。
- `managed_replace`、`layered`、`init_only`、`report_only`。
- `.agents/agentphilosophy-state.yaml` hash 检查。
- `source_revision` / `source_tree_hash` 记录。
- 轻量 preset 展开到项目根目录正式 `.agentphilosophy.yaml`。
- `init --interactive` 的交互式配置生成。
- 模块 `requires` / `conflicts` / `project_types` 校验。
- `catalog.yaml` 基础校验。
- 路径越界保护。
- `--dry-run`、`--prune-managed` 和迁移报告。

暂缓实现：

- 自动语义拆分旧 `AGENTS.md` / `CLAUDE.md`。
- 自动把旧 spec 内容归并到 custom。
- 会覆盖已有正式配置的迁移草稿提升。
- `pull` 反向同步。
- 复杂 preset 生成器或动态 preset 继承。

## 十六、验收标准

本设计进入实现前必须满足：

- 文档不再把模块级 `mode` 当成唯一执行分支。
- 老项目已有文件默认不会被覆盖。
- ExampleMobileSDKProject 的 `docs/guide`、ExampleOrchestratorProject 的 `skills/`、ExampleFrontendProject 的 `ArchitectureSpec/TestStrategy` 都有对应设计入口。
- 模板组合统一使用已定义的 `section(name)` 函数注入片段。
- sync 状态不污染用户手写 `.agentphilosophy.yaml`。
- 第一版 migrate 明确是报告工具，不是自动改写工具。
- 新项目可以通过 `init --preset` 快速生成配置草稿。
- 老项目可以通过 `migrate -> 审核草稿配置 -> 写入正式 .agentphilosophy.yaml -> adopt -> push --dry-run -> push --apply` 安全接入；如果提供 `migrate --write-config`，也只能在正式配置不存在时执行这一步。
- 中央源和目标项目都可以通过 `validate` 独立校验。
- state 能追溯到中央源 revision 或 tree hash。
