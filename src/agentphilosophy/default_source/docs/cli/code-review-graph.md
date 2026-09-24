## 十一、code-review-graph 结构图谱依赖

AgentPhilosophy 固定依赖 `code-review-graph==2.3.9`，并通过 `pyproject.toml` 重新导出同名 `code-review-graph` CLI。默认 preset 还会包含 `skill-code-review-graph`，将 `SKILL.md`、`agents/openai.yaml` 和 MIT 许可证同步到仓库级与 Codex 项目级 skill 目录。

从 2.3.8 升级会自动迁移本地图谱 schema；先备份 `.code-review-graph/graph.db`，升级后完整运行一次 `code-review-graph build --repo .`。回退旧版需要重建图谱，详细步骤见 [使用指南](../guides/code-review-graph.md)。

三层入口的职责必须区分：

- Skill 负责触发和编排，不执行图谱解析。
- MCP 是 agent 日常查询最小上下文、影响半径、改动风险、调用关系、流程和测试关系的主要入口。
- CLI 负责安装 MCP、首次构建、增量更新、状态、watch、可视化和人工诊断。

上游 `install --platform codex` 会写用户级 Codex MCP 与 hooks 配置，并可能修改项目 `AGENTS.md` 和 Git hook；没有明确安装意图时先运行 `--dry-run`。正式安装后需要重启 Codex：

```bash
code-review-graph install --platform codex --repo . --dry-run
code-review-graph install --platform codex --repo . --yes
code-review-graph build --repo .
code-review-graph status --repo .
```

旧项目的模块列表是显式冻结的。需要长期同步图谱 skill 时，在保留已有模块的基础上追加：

```yaml
modules:
  - existing-module
  - skill-code-review-graph
```

然后按 `validate`、目标项目 dry-run、apply、status 的标准顺序同步。完整用法见 [docs/guides/code-review-graph.md](../guides/code-review-graph.md)。
