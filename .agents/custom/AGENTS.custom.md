## Agent 导航入口

- Matt skills 项目级 setup、issue、triage、领域资料与明确排除项统一从 `docs/agents/README.md` 进入。
- 中央内容维护先读 `docs/agents/maintenance.md`，CLI 操作按 `docs/cli-usage-for-llm.md` 的任务入口读取相关章节。
- 修改中央 `modules/`、`presets/`、`templates/` 或项目 custom 源，通过 `scripts/sync-packaged-source.py --apply` 刷新包内镜像，再用同步 CLI 更新本仓生成结果；不手改托管 AGENTS、skills 或 state。
- 本仓验证入口：`uv run --locked ruff check .`、`uv run --locked pytest -q`、`uv run --locked sync.py validate`。完整长期文档索引是 `docs/README.md`。
- 仓库日常维护使用 `loop-check`；具体检查项、授权范围和触发方式见 `.agents/custom/loop-check.md`。
