## 变更摘要

- 发布 AgentPhilosophy CLI v0.7.7。
- 默认内容源 `content_version` 升级到 `0.7.7`。
- `model-constraints` 升级到 `1.1.0`，多 Agent 规则改为按任务风险、复杂度和验证难度选择模型与推理强度，并收紧并行与写入边界。
- 默认 preset 不再启用 `superpowers-system`；该模块仍作为显式可选能力保留，既有显式启用配置继续兼容。
- 自动摘要基于 `v0.7.6` 到当前工作树、模块版本变化和最近提交生成。
- 本次版本相关 diff 涉及 `33` 个文件，主要集中在 CLI/脚本、中央内容源、文档、测试/验证。
- 检测到模块版本变化：`model-constraints`。
- 最近提交参考：文档：统一 Superpowers 可选接入合同。

## 本次 diff 重点

- CLI/脚本：`pyproject.toml`、`scripts/release-smoke.sh`、`src/agentphilosophy/__init__.py`、`uv.lock`。
- 中央内容源：`catalog.yaml`、`modules/model-constraints/module.yaml`、`modules/model-constraints/templates/model-rules.md.j2`、`presets/frontend.yaml`、`presets/fullstack.yaml`、`presets/mobile-sdk.yaml` 等 12 个文件。
- 测试/验证：`tests/bdd/test_user_flows.py`、`tests/e2e/test_sync_cli.py`、`tests/test_ci_release_gate.py`。
- 文档：`README.md`、`docs/README.md`、`docs/cli-usage-for-llm.md`、`docs/llm-usage-auto-config.md`、`docs/llm-usage-user-breakpoints.json`、`docs/llm-usage-user-breakpoints.md`。

## 模块版本变化

- `model-constraints`：`1.0.0` -> `1.1.0`，多 Agent 模型、推理强度和代理调度约束。

## 最近提交参考

- 文档：统一 Superpowers 可选接入合同
- 配置：将 Superpowers 调整为项目显式可选
- 规范：按任务选择多 Agent 模型与推理强度
- 计划：拆分灵活多 Agent 与可选 Superpowers 实施步骤
- 设计：明确灵活多 Agent 与可选 Superpowers 边界

## 依赖项目影响

- `agentphilosophy_version` 会写入依赖项目的同步状态。
- `source_content_version` 用于提示依赖项目是否需要同步新一轮中央内容。
- 默认内容源有文件变化，依赖项目同步前先运行 `push --dry-run` 审查托管输出计划。
- 依赖项目可能看到 `module version stale`，优先审查 `model-constraints` 对应输出。
- 发版后运行 `uv run sync.py status` 查看 registry 中依赖项目是否 stale。

## 验证

- `uv run ruff check .`
- `uv run pytest -q`
- `uv run sync.py validate`
- `uv run sync.py status --project .`
- `uv lock --check`
- `uv build`
- `bash scripts/release-smoke.sh dist/agentphilosophy-0.7.7-py3-none-any.whl`
