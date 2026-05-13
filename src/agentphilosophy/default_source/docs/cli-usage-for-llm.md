# AgentPhilosophy CLI 使用说明（给 LLM）

本文只记录当前程序已经实现的 CLI 行为。LLM 执行项目配置任务时，应以本文为准；设计文档中的未来能力不得当成已可用功能。

## 一、运行前提

- 默认在 AgentPhilosophy 仓库根目录运行命令。
- 使用 `uv run sync.py ...` 调用当前源码。
- 如果已经安装 CLI，也可以使用 `agentphilosophy-sync ...`。安装后的 CLI 在当前目录不是中央规范源时，会自动使用包内规范源。
- 命令是否可用以 `uv run sync.py <command> --help` 为准；不要把设计文档里的未来能力当成当前可执行参数。
- 如果从其他目录调用，使用全局参数指定中央源：

```bash
uv run /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy validate
uv run /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy push /path/to/project --dry-run
```

安装 CLI 后的等价入口：

```bash
agentphilosophy-sync validate
agentphilosophy-sync llm-usage
agentphilosophy-sync init /path/to/project --preset fullstack
agentphilosophy-sync push /path/to/project --dry-run
```

## 二、真实可用命令

查看帮助：

```bash
uv run sync.py --help
uv run sync.py init --help
uv run sync.py push --help
uv run sync.py migrate --help
uv run sync.py adopt --help
uv run sync.py status --help
uv run sync.py llm-usage --help
```

校验中央源：

```bash
uv run sync.py validate
```

校验目标项目配置和渲染结果：

```bash
uv run sync.py validate /path/to/project
```

输出给 LLM 使用的当前 CLI 说明：

```bash
uv run sync.py llm-usage
```

初始化新项目配置：

```bash
uv run sync.py init /path/to/project --preset mobile-sdk
uv run sync.py init /path/to/project --interactive
```

`init --interactive` 会提示输入 `preset`、`project_name`、`project_type`、`description`、`test_command`，并写入目标项目根目录 `.agentphilosophy.yaml`。它只生成配置，不渲染托管输出，也不自动执行 `push --dry-run` 或 `push --apply`。

安全预览同步计划：

```bash
uv run sync.py push /path/to/project --dry-run
```

应用同步计划：

```bash
uv run sync.py push /path/to/project --apply
```

迁移盘点老项目：

```bash
uv run sync.py migrate /path/to/project
```

当前 `uv run sync.py migrate --help` 已列出 `--write-config`，可执行：

```bash
uv run sync.py migrate /path/to/project --write-config
```

`migrate --write-config` 的边界必须保持严格：先生成 `.agents/migration/proposed.agentphilosophy.yaml` 等迁移草稿；仅当项目根目录 `.agentphilosophy.yaml` 不存在时，才把迁移草稿写入正式配置。若正式配置已存在，必须拒绝覆盖。该参数不接管文件、不写托管输出，也不替代后续 `validate`、`adopt`、`push --dry-run`。

登记接管单个既有文件：

```bash
uv run sync.py adopt /path/to/project --file AGENTS.md --module doc-templates --output agents-md
```

按迁移报告登记接管文件：

```bash
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
```

查看目标项目状态：

```bash
uv run sync.py status --project /path/to/project
```

清理已从当前配置移除且未被手动改动的托管文件：

```bash
uv run sync.py push /path/to/project --prune-managed
```

批量查看或同步 `registry.yaml` 中的项目：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
uv run sync.py push --all --apply
```

批量同步要求 registry 中的目标项目已经存在正式 `.agentphilosophy.yaml`。未接入的项目应先按新项目或老项目迁移流程补齐配置。

`push --prune-managed` 只能针对明确的单个目标项目执行，不能和 `--dry-run`、`--apply` 或 `--all` 混用。它的安全条件是：

- 目标文件必须在 `.agents/agentphilosophy-state.yaml` 中登记过。
- 当前 `.agentphilosophy.yaml` 渲染结果已经不再包含该输出路径。
- 目标文件仍存在时，当前 hash 必须等于 state 里的 `last_written_hash`。
- 文件有手动改动时必须拒绝删除。
- 文件已经缺失时，只清理 state 记录。
- 成功删除文件后，会尝试删除该文件的直接空目录；不会继续向上清理项目父目录。

## 三、版本与更新判断

AgentPhilosophy 使用三层版本判断目标项目是否需要更新：

- CLI 工具版本来自 `pyproject.toml` 和 `agentphilosophy.__version__`，只表示同步程序自身版本。
- 中央规范内容源版本来自 `catalog.yaml` 的 `content_version`，用于判断依赖项目是否需要同步新一轮中央内容。
- 单个模块版本来自各 `module.yaml` 的 `version`，用于判断具体模块是否 stale。

`agentphilosophy-sync --version` 用于确认当前安装的 CLI release 版本。`push --apply` 和 `adopt` 会把当前 `agentphilosophy_version` 与 `source_content_version` 写入目标项目 `.agents/agentphilosophy-state.yaml`；`status --project` 如果发现 state 中 CLI 版本落后于当前安装包，会输出 `agentphilosophy_version stale: <old> -> <new>`，如果发现内容源版本落后于当前中央源，会输出 `source_content_version stale: <old> -> <new>`。看到 stale 提示时，先运行 `push /path/to/project --dry-run` 审查计划，再决定是否 `--apply`。

如果 state 中的版本高于当前中央源或当前 CLI，`status` 会提示 `source_content_version newer than current source` 或 `agentphilosophy_version newer than current CLI`；此时先检查是否误用了旧的 `--source`、旧安装包或回退后的中央源，不要直接覆盖目标项目。`source_tree_hash` 是源文件指纹，`catalog.yaml` 变更可能同时触发 hash drift 和内容版本提示。

## 四、目标项目配置

目标项目根目录使用 `.agentphilosophy.yaml` 声明配置。CLI 不从该文件读取中央源路径；中央源由当前工作目录或 `--source` 参数决定。

最小示例：

```yaml
project_name: DemoProject
project_type: mobile-sdk
preset: mobile-sdk
description: 移动 SDK 项目

paths:
  docs_guide_dir: docs/guide
  spec_dir: spec

skill_targets:
  repo_skills: skills
  codex_project: .codex/skills
  claude_project: .claude/skills

modules:
  - openspec-skills
  - jj-conventions
  - model-constraints
  - doc-templates
  - multi-module-layout
  - spec-program
  - spec-ddd
  - spec-bdd
  - spec-test-mobile
  - spec-test-general
  - spec-architecture
  - skill-agentphilosophy-sync
  - skill-jj-management
  - skill-target-jj
  - skill-coding-standards
  - skill-repo-management
  - aphilosophy

vars:
  primary_tool: Codex CLI
  test_command: ./scripts/run_tests.sh
```

常用 preset：

- `orchestrator`：编排器项目。
- `fullstack`：前后端、部署和 OpenSpec 项目。
- `frontend`：前端主导项目。
- `mobile-sdk`：移动 SDK 或多子工程工作区。

这些 preset 默认包含 `jj-conventions` 和 `skill-jj-management`。LLM 接入目标项目时，如果目标项目是 Git 仓库但还没有 `.jj/`，应先确认 `command -v jj && jj --version`，缺失时安装 jj CLI，然后运行 `jj git init --colocate`，再用 `jj status`、`jj log`、`jj bookmark list` 验证。

常用路径：

- `paths.docs_guide_dir`：项目 guide 文档目录，默认 `docs/guides`。
- `paths.spec_dir`：spec 文档目录，默认 `spec`。
- `paths.philosophy_dir`：Agent 哲学决策框架目录，默认 `aphilosophy`。
- `paths.migration_dir`：迁移报告目录，默认 `.agents/migration`。
- `skill_targets.repo_skills`：仓库级 skills 目录，默认 `skills`。
- `skill_targets.codex_project`：Codex 原生项目级 skill discovery 目录，默认 `.codex/skills`。需要让 Codex 自动发现项目级 skill 时保持该默认值，并在 `push --apply` 后验证 `.codex/skills/**/SKILL.md` 存在。
- `skill_targets.claude_project`：Claude 项目级 skills 目录，默认 `.claude/skills`。

## 五、Agent 哲学决策框架

`aphilosophy` 模块会生成一组触发式参考文档。LLM 不需要在每次任务开始时全量读取它们；只有当任务进入对应冲突或权衡场景时，才按需读取。

- 遇到指令冲突、任务妥协、不确定性或连续尝试失败时，读取 `aphilosophy/meta-decision-principles.md`。
- 遇到架构设计、技术选型、抽象层增减、配置化取舍或系统退化判断时，读取 `aphilosophy/architecture-conflict-resolution.md`。
- 遇到多 Agent 协作、角色边界、用户沟通、命名歧义、治理层级或行为校准问题时，读取 `aphilosophy/governance-conflict-resolution.md`。

这些文档是通用决策锚点，不覆盖项目自己的 `AGENTS.md`、`spec/` 或 `.agents/custom` 规则。若哲学框架与项目特定规范冲突，以项目特定规范为准；若项目规范前提已经失效，应先向用户说明观察到的事实，再提出可验证的调整建议。

## 六、Registry 文件

`registry.yaml` 位于 AgentPhilosophy 中央源根目录，是本机真实批量入口。它可以记录本机绝对路径，且已加入 `.gitignore`，供以下命令读取：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
uv run sync.py push --all --apply
```

`registry.example.yaml` 是可复用模板。新机器或新使用者应复制它为 `registry.yaml`，再把 `path` 改成本机真实路径；不要把 `registry.example.yaml` 当作真实批量同步入口。

示例结构：

```yaml
schema_version: 1
projects:
  - name: ExampleProject
    path: /absolute/path/to/ExampleProject
```

## 七、新项目接入流程

1. 选择 preset。
2. 生成 `.agentphilosophy.yaml`。
3. 校验目标项目。
4. 先 dry-run，确认没有冲突。
5. 再 apply。
6. 最后查看状态。

```bash
uv run sync.py init /path/to/project --preset fullstack
uv run sync.py validate /path/to/project
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
uv run sync.py status --project /path/to/project
```

如果需要交互确认项目名、项目类型、描述或测试命令，使用：

```bash
uv run sync.py init /path/to/project --interactive
```

## 八、老项目迁移流程

`migrate` 只做盘点，不会生成正式 `.agentphilosophy.yaml`，也不会覆盖项目已有文件。

```bash
uv run sync.py migrate /path/to/project
```

迁移产物在目标项目的 `.agents/migration/` 下：

- `inventory.md`：既有 Agent、Spec、Skill 文件清单，包括 `skills/`、`.codex/skills/` 和 `.claude/skills/` 下的 `SKILL.md`。
- `proposed.agentphilosophy.yaml`：建议配置草稿。
- `adopt-plan.yaml`：可接管文件清单。
- `diffs/`：候选输出文件。

LLM 必须先检查这些产物。确认配置草稿可用后，再把它作为项目根目录 `.agentphilosophy.yaml`，或使用 `migrate --write-config` 安全写入正式配置。

`migrate --write-config` 只允许在 `.agentphilosophy.yaml` 不存在时从迁移草稿写入正式配置；如果正式配置已存在，必须拒绝覆盖。写入正式配置后，仍然必须继续执行：

```bash
uv run sync.py validate /path/to/project
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
```

## 九、安全边界

- `push` 不带 `--apply` 时不写目标项目文件；`--dry-run` 是推荐显式写法。
- `push --apply` 也不会覆盖未托管的既有文件；遇到冲突会写候选文件到迁移目录。
- `adopt` 不修改目标文件内容，只把当前文件 hash 写入 `.agents/agentphilosophy-state.yaml`。
- `migrate` 只写 `.agents/migration/` 下的报告和候选文件。
- `push --prune-managed` 只清理 state 中登记、当前 hash 仍匹配、且已从当前配置输出中移除的托管文件；文件有手动改动时会拒绝清理。
- `migrate --write-config` 若可用，只能在正式 `.agentphilosophy.yaml` 不存在时写入；存在时必须拒绝覆盖。
- 不要把 `.agents/migration/proposed.agentphilosophy.yaml` 当成正式配置；`push` 只读取项目根目录 `.agentphilosophy.yaml`。
- 修改 `modules` 后必须重新运行 `validate` 和 `push --dry-run`。

## 十、LLM 执行规则

- 操作前先运行 `uv run sync.py validate`，确认中央源有效。
- 对目标项目写入前必须先运行 `push --dry-run`。
- 读取 `aphilosophy/` 文档应按场景触发，不要把它们当成每次任务的必读上下文。
- 执行可选参数前先看对应 `--help`；帮助里没有的参数不要执行。
- 如果 CLI 输出 `[error]`，停止写入并回报具体错误。
- 如果 CLI 输出 `[warning]`，继续前先判断 warning 是否影响本次目标。
- 不要手工编辑 `.agents/agentphilosophy-state.yaml`。
- 不要把未来设计当成当前能力。
