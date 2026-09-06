## 十八、老项目迁移流程

`migrate` 只做盘点，不会生成正式 `.agentphilosophy.yaml`，也不会覆盖项目已有文件。

```bash
uv run sync.py migrate /path/to/project
```

迁移产物在目标项目的 `.agents/migration/` 下：

- `inventory.md`：既有 Agent、Spec、Skill 文件清单，包括 `skills/`、`.agents/skills/` 和 `.claude/skills/` 下的 `SKILL.md`。
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
