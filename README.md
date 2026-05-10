# AgentPhilosophy

AgentPhilosophy 是中央 Agent 协作规范管理仓库，用于把共享的 Agent 文档、Spec 规范和项目级 skills 按配置同步到目标项目。

## 常用命令

```bash
uv run sync.py validate
uv run sync.py init /path/to/project --preset fullstack
uv run sync.py init /path/to/project --interactive
uv run sync.py migrate /path/to/project
uv run sync.py migrate /path/to/project --write-config
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
uv run sync.py push /path/to/project --prune-managed
uv run sync.py status --project /path/to/project
```

`init --interactive` 用于交互式生成目标项目根目录 `.agentphilosophy.yaml`，适合还没有确定 preset、项目类型、描述或测试命令的新项目；它不会渲染托管输出，也不会自动执行 `push`。

批量入口读取仓库根目录 `registry.yaml`；批量同步要求目标项目已经存在 `.agentphilosophy.yaml`：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
```

## Registry 文件

- `registry.yaml` 是本机真实批量入口，可以包含本机绝对路径；`status` 不带 `--project`、`push --all` 都读取它。
- `registry.example.yaml` 是可复用模板，用于复制成新的本机 `registry.yaml` 后再改路径，不应作为真实批量同步入口。
- `registry.yaml` 已加入 `.gitignore`，避免把个人路径和批量目标误提交。

## 安全边界

- `push --prune-managed` 只接受明确的单个目标项目路径，不能和 `--dry-run`、`--apply` 或 `--all` 混用。
- prune 只会处理 state 中登记过、当前文件 hash 仍等于 `last_written_hash`、且已经从当前 `.agentphilosophy.yaml` 渲染输出中移除的托管文件。
- 如果文件被手动改过，prune 必须拒绝删除；缺失文件只会清理 state 记录。
- prune 会尝试删除被删文件的直接空目录，但不会继续向上清理项目父目录。
- `migrate --write-config` 只能在目标项目根目录 `.agentphilosophy.yaml` 不存在时，把 `.agents/migration/proposed.agentphilosophy.yaml` 写入正式配置；已存在正式配置时必须拒绝覆盖。

`pull` 当前仍是占位命令；第一版推荐从 AgentPhilosophy 中央源向目标项目执行 `push`。

## LLM 操作说明

给 LLM 或自动化 agent 使用时，优先阅读：

- [docs/cli-usage-for-llm.md](docs/cli-usage-for-llm.md)

执行任何目标项目写入前，先运行：

```bash
uv run sync.py validate
uv run sync.py push /path/to/project --dry-run
```
