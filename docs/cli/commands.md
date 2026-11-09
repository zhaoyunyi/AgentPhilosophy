## 二、真实可用命令

1.3.0 新增独立项目的 `check-update`、`upgrade` 和 `rollback`；版本引导、目标 JSON、差异、退出码与恢复方式见 [升级与回退](upgrade.md)。v1.2.2 不包含这三个命令。

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
uv run sync.py llm-usage --mode auto-config
uv run sync.py llm-usage --mode user-breakpoints
uv run sync.py llm-usage --mode user-breakpoints --format json
```

`llm-usage` 默认输出完整 CLI 说明，输出格式默认为 Markdown。`--mode auto-config` 输出“LLM 根据项目事实自动选择配置并安装”的精简协议；`--mode user-breakpoints` 输出“LLM 返回用户断点、由用户选择配置后再安装”的精简协议。用户没有明确授权自动选择配置时，优先使用 `user-breakpoints`，并让断点问题包含推荐项、选项影响和回复方式。需要让 agent 直接读取断点标题、推荐项、选项列表和回复格式时，使用 `llm-usage --mode user-breakpoints --format json`。

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

批量应用同步成功后，可为本轮确实发生 CLI 版本、内容版本、模块版本或托管输出变化的项目调用大模型更新项目自有文档：

```bash
uv run sync.py push --all --apply \
  --project-name ExampleFullstack \
  --update-docs \
  --llm-command 'codex exec --ephemeral --ignore-user-config --sandbox workspace-write -'
```

每个需要更新文档的 registry 项目必须显式声明项目根目录内的相对路径：

```yaml
projects:
  - name: ExampleFullstack
    path: /absolute/path/to/ExampleFullstack
    documentation_paths:
      - README.md
      - docs
```

`--project-name <名称>` 可重复提供，只处理 registry 中名称完全匹配的项目；未知名称会报错，省略时处理全部登记项目。`--llm-command` 只接受 `codex exec`，并强制要求 `--ephemeral --ignore-user-config --sandbox workspace-write -`；额外可写目录、切换工作根目录、自定义 profile/config、任意输出文件和绕过 sandbox 的参数都会被拒绝。模型任务通过标准输入传入。可用 `--llm-timeout <秒>` 调整每个项目的超时，默认 900 秒。该功能只接受 `--all --apply`：已经完成当前版本文档刷新的项目、同步失败的项目和未声明 `documentation_paths` 的项目不会调用模型。模型完成后 CLI 会复查 state 中登记的全部托管文件、保护文件、版本控制元数据以及文档白名单外的项目文件；任何越界改动都会使当前项目失败，但不会阻断后续 registry 项目。只有成功时才写入包含 `documentation_paths` 的 `documentation_refresh` 指纹，因此模型失败、超时、越界配置、保护漂移或文档范围扩大后可以重试。CLI 不会自动提交、推送或发布文档改动。

`push --prune-managed` 只能针对明确的单个目标项目执行，不能和 `--dry-run`、`--apply` 或 `--all` 混用。它的安全条件是：

- 目标文件必须在 `.agents/agentphilosophy-state.yaml` 中登记过。
- 当前 `.agentphilosophy.yaml` 渲染结果已经不再包含该输出路径。
- 目标文件仍存在时，当前 hash 必须等于 state 里的 `last_written_hash`。
- 文件有手动改动时必须拒绝删除。
- 文件已经缺失时，只清理 state 记录。
- 成功删除文件后，会尝试删除该文件的直接空目录；不会继续向上清理项目父目录。
