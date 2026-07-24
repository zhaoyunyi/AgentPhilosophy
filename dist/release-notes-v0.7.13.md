## 变更摘要

- 发布 AgentPhilosophy CLI v0.7.13。
- 默认内容源 `content_version` 升级到 `0.7.13`。
- 自动摘要基于`v0.7.12` 到当前工作树、模块版本变化和最近提交生成。
- 本次版本相关 diff 涉及 `44` 个文件，主要集中在 CLI/脚本、中央内容源、文档、测试/验证。
- 检测到模块版本变化：`skill-optimize-build-pipeline`。
- 最近提交参考：技能：新增完整构建流水线调优流程。

## 本次 diff 重点

- CLI/脚本：`pyproject.toml`、`src/agentphilosophy/__init__.py`、`uv.lock`。
- 中央内容源：`catalog.yaml`、`modules/skill-optimize-build-pipeline/module.yaml`、`modules/skill-optimize-build-pipeline/optimize-build-pipeline/SKILL.md`、`modules/skill-optimize-build-pipeline/optimize-build-pipeline/agents/openai.yaml`、`modules/skill-optimize-build-pipeline/optimize-build-pipeline/references/measurement-contract.md`、`modules/skill-optimize-build-pipeline/optimize-build-pipeline/references/optimization-playbook.md` 等 20 个文件。
- 测试/验证：`tests/bdd/test_cli_baseline_flows.py`、`tests/e2e/test_sync_cli.py`、`tests/test_optimize_build_pipeline_skill.py`、`tests/test_packaged_source.py`。
- 文档：`README.md`、`docs/README.md`、`docs/agents/README.md`、`docs/agents/domain.md`、`docs/agents/issue-tracker.md`、`docs/agents/out-of-scope/README.md` 等 5 个文件。

## 模块版本变化

- `skill-optimize-build-pipeline`：新增 `version` `1.0.0`，完整墙钟、硬件证据、缓存、并行与 registry receipt 驱动的构建流水线调优 skill。

## 最近提交参考

- 技能：新增完整构建流水线调优流程
- 同步：刷新依赖项目导航状态
- 文档：建立统一 Agent 导航入口
- 文档：将稳定安装入口更新到 v0.7.12

## 依赖项目影响

- `agentphilosophy_version` 会写入依赖项目的同步状态。
- `source_content_version` 用于提示依赖项目是否需要同步新一轮中央内容。
- 默认内容源有文件变化，依赖项目同步前先运行 `push --dry-run` 审查托管输出计划。
- 依赖项目可能看到 `module version stale`，优先审查 `skill-optimize-build-pipeline` 对应输出。
- 发版后运行 `uv run sync.py status` 查看 registry 中依赖项目是否 stale。

## 本次未纳入

- 发布 preflight 检测到 Matt Pocock 相关模块和 Portless 的上游 `main` 已有新 revision；这些更新与本次构建流水线调优技能无关，且尚未完成独立审查，因此保持现有锁定值，留待后续单独升级和发布。

## 验证

- `uv run ruff check .`
- `uv run pytest -q`
- `uv run sync.py validate`
- `uv build`
- `bash scripts/release-smoke.sh dist/agentphilosophy-0.7.13-py3-none-any.whl`
