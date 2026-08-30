# AgentPhilosophy

AgentPhilosophy 是中央 Agent 协作规范管理仓库，用于把共享的 Agent 文档、Spec 规范和项目级 skills 按配置同步到目标项目。

默认同步会同时写入仓库级 `skills/` 和 Codex 原生项目级 `.codex/skills/`，后者用于让 Codex skill discovery 在进入项目后自动发现并按 frontmatter 触发。

## 快速开始

### 源码仓库使用

```bash
git clone git@github.com:zhaoyunyi/AgentPhilosophy.git
cd AgentPhilosophy
uv run sync.py validate
uv run sync.py --version
uv run sync.py init /path/to/project --preset fullstack
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
```

### 安装 CLI 后使用

安装后的 CLI 默认使用包内规范源；只有需要指定自定义中央源时才传 `--source`。

```bash
uv tool install git+ssh://git@github.com/zhaoyunyi/AgentPhilosophy.git@v0.8.0
```

需要跟随 `main` 最新内容时再使用：

```bash
uv tool install git+ssh://git@github.com/zhaoyunyi/AgentPhilosophy.git
```

后续未发布到稳定 tag 的内容源更新需要安装 `main` 最新内容；固定 tag 只代表对应 release 已包含的内容源。

安装后：

```bash
agentphilosophy-sync validate
agentphilosophy-sync llm-usage
agentphilosophy-sync llm-usage --mode auto-config
agentphilosophy-sync llm-usage --mode user-breakpoints
agentphilosophy-sync init /path/to/project --preset fullstack
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
code-review-graph --version
```

AgentPhilosophy 固定依赖 `code-review-graph==2.3.8`，并重新导出同名 CLI。默认 preset 还会同步 `code-review-graph` 项目级 skill，用于让 agent 在审查、影响分析、调试、架构探索和安全重构时优先通过 MCP 获取结构化最小上下文。首次配置、构建、状态、watch 和可视化仍由 CLI 完成，详见 [code-review-graph 使用指南](docs/guides/code-review-graph.md)。

安装 `main` 最新内容后，还可以让 agent 直接读取用户断点结构化数据：

```bash
agentphilosophy-sync llm-usage --mode user-breakpoints --format json
```

如果目标项目已经有 `AGENTS.md`、`spec/` 或 `skills/` 等历史内容，先走迁移流程：

```bash
agentphilosophy-sync migrate /path/to/project
agentphilosophy-sync migrate /path/to/project --write-config
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

## 给 LLM 的入口

让 LLM 或自动化 agent 操作本仓库时，先读：

- [docs/README.md](docs/README.md)
- [docs/cli-usage-for-llm.md](docs/cli-usage-for-llm.md)
- [docs/release-process.md](docs/release-process.md)
- [release-notes/README.md](release-notes/README.md)
- [docs/guides/aphilosophy-methodology.md](docs/guides/aphilosophy-methodology.md)

文档索引记录 `docs/` 下长期文档入口，新增长期文档时必须同步更新。CLI 使用文档记录当前已经实现的行为，包括新项目接入、老项目迁移、批量 registry、`superpowers-system` 可选的原生 discovery 版本约束、`code-review-graph` 依赖、MCP 与项目级 skill 的分层用法、可选安装的 `skill-ponytail` 精简编码 skill、`skill-reverse-skill` 授权逆向路由 skill、Matt Pocock 22 个活跃 skills 的完整工程能力集与 `docs/agents/` 设置目录、默认 preset 内置的完整构建流水线调优、Grok CLI headless 编排审查和 Portless 本地开发入口判断 skill、可选独立 `skill-code-review` 审查 skill、`aphilosophy/` 决策框架的触发式读取规则、可选 `skill-philosophy-extraction` 哲学脱水 skill，以及写入前必须执行的校验步骤。`llm-usage --mode auto-config` 用于 LLM 根据项目事实自动选择配置并安装；`llm-usage --mode user-breakpoints` 用于 LLM 返回清晰断点，让用户选择配置后再安装；`llm-usage --mode user-breakpoints --format json` 用于 agent 直接读取断点标题、推荐项、选项列表和回复格式。发版文档记录版本口径、外部 skill 上游 revision 检查、准备脚本、发布脚本和依赖项目更新判断；`aphilosophy` 方法论文档用于维护或扩展哲学决策框架时确认脱水标准和模板索引。

## 常用命令

```bash
uv run sync.py validate
uv run sync.py init /path/to/project --preset fullstack
uv run sync.py init /path/to/project --interactive
uv run sync.py llm-usage
uv run sync.py llm-usage --mode auto-config
uv run sync.py llm-usage --mode user-breakpoints
uv run sync.py llm-usage --mode user-breakpoints --format json
uv run sync.py migrate /path/to/project
uv run sync.py migrate /path/to/project --write-config
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
uv run sync.py push /path/to/project --prune-managed
uv run sync.py status --project /path/to/project
```

## 版本口径

AgentPhilosophy 使用三层版本描述中央源与目标项目的同步状态：

- `pyproject.toml` / `agentphilosophy.__version__` 表示 CLI 工具版本。
- `catalog.yaml` 的 `content_version` 表示中央规范内容源整体版本，用于依赖项目判断是否需要更新一轮。
- 各 `module.yaml` 的 `version` 表示单个模块版本，用于 `status` 判断目标项目中具体模块是否 stale。

`push --apply` 和 `adopt` 会把当前 `agentphilosophy_version` 与 `source_content_version` 写入目标项目 `.agents/agentphilosophy-state.yaml`。后续 `status --project` 会在 state 中的 CLI 版本落后于当前安装包时提示 `agentphilosophy_version stale`，在内容源版本落后于当前中央源时提示 `source_content_version stale`。如果 state 版本高于当前中央源或当前 CLI，先检查是否误用了旧的 `--source`、旧安装包或回退后的中央源。`source_tree_hash` 是源文件指纹，`catalog.yaml` 变更可能同时触发 hash drift 和内容版本提示。

`init --interactive` 用于交互式生成目标项目根目录 `.agentphilosophy.yaml`，适合还没有确定 preset、项目类型、描述或测试命令的新项目；它不会渲染托管输出，也不会自动执行 `push`。

批量入口读取仓库根目录 `registry.yaml`；批量同步要求目标项目已经存在 `.agentphilosophy.yaml`：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
```

依赖项目同步成功后，可以对本轮确实发生版本、模块或托管输出变化的项目调用大模型更新项目自有文档。先在 `registry.yaml` 的项目条目中声明 `documentation_paths`，再显式执行：

```bash
uv run sync.py push --all --apply \
  --project-name ExampleFullstack \
  --update-docs \
  --llm-command 'codex exec --ephemeral --ignore-user-config --sandbox workspace-write -'
```

`--project-name` 可重复提供，用于只更新 registry 中点名的项目；省略时仍处理全部登记项目。模型命令必须使用 `codex exec --ephemeral --ignore-user-config --sandbox workspace-write -` 的受限执行合同，不允许额外可写目录、切换工作根目录、加载自定义 profile/config 或输出到任意文件。任务提示通过标准输入传入；已经完成当前版本文档刷新、同步冲突或未声明文档范围的项目不会调用模型。CLI 会在模型完成后复查所有 AgentPhilosophy 托管文件、保护文件、版本控制元数据以及允许文档范围外的项目文件，只在成功后记录包含文档路径的刷新指纹，因此失败原因修复或文档范围扩大后可以重试；它不会自动提交、推送或发布文档改动。

## Registry 文件

- `registry.yaml` 是本机真实批量入口，可以包含本机绝对路径；`status` 不带 `--project`、`push --all` 都读取它。
- `registry.example.yaml` 是可复用模板，用于复制成新的本机 `registry.yaml` 后再改路径，不应作为真实批量同步入口。
- `registry.yaml` 已加入 `.gitignore`，避免把个人路径和批量目标误提交。
- `documentation_paths` 是项目级相对路径白名单，只用于显式启用的批量大模型文档更新阶段。

## 安全边界

- `push --prune-managed` 只接受明确的单个目标项目路径，不能和 `--dry-run`、`--apply` 或 `--all` 混用。
- prune 只会处理 state 中登记过、当前文件 hash 仍等于 `last_written_hash`、且已经从当前 `.agentphilosophy.yaml` 渲染输出中移除的托管文件。
- 如果文件被手动改过，prune 必须拒绝删除；缺失文件只会清理 state 记录。
- prune 会尝试删除被删文件的直接空目录，但不会继续向上清理项目父目录。
- `migrate --write-config` 只能在目标项目根目录 `.agentphilosophy.yaml` 不存在时，把 `.agents/migration/proposed.agentphilosophy.yaml` 写入正式配置；已存在正式配置时必须拒绝覆盖。
- `push --update-docs` 只能与 `--all --apply --llm-command` 组合；可用可重复的 `--project-name` 缩小批量范围。未使用受限 Codex sandbox 合同，或模型改动托管文件、保护文件、版本控制元数据、`documentation_paths` 外文件时，命令会失败并报告漂移。

默认 preset 会启用 jj colocated git 管理规则。目标项目是普通 Git 仓库但还没有 `.jj/` 时，先确认或安装 jj CLI，再执行 `jj git init --colocate`，最后用 `jj status` / `jj log` / `jj bookmark list` 验证。

执行任何目标项目写入前，先运行：

```bash
uv run sync.py validate
uv run sync.py push /path/to/project --dry-run
```
