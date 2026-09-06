# 中央源维护入口

适用于修改 AgentPhilosophy 的同步程序、中央规则或 skill。目标项目接入与迁移按 [CLI 任务索引](../cli-usage-for-llm.md) 操作。

## 先确定写入来源

| 任务 | 权威位置与验证 |
| --- | --- |
| 同步/迁移/状态行为 | `src/agentphilosophy/`，对应 CLI、BDD 与 E2E 测试 |
| 通用规则、skill 与资源 | `modules/*/module.yaml` 和该模块的 templates/files；语义变化提升模块版本 |
| 默认项目组合与目录 | `presets/` 与 `src/agentphilosophy/project.py`，验证新项目及旧配置兼容 |
| 本仓特有说明 | `.agents/custom/`，随后同步生成 AGENTS/spec/release 索引 |
| 包内默认源 | 由 `scripts/sync-packaged-source.py` 刷新，维护者不逐份手改 |
| 文档 | 修改 `docs/cli/` 对应单页及 `docs/README.md`；`llm-usage` 按入口清单组装全文 |
| 发布 | [发布流程](../release-process.md)，从固定提交构建并核对制品回执 |
| 外部 skill | `scripts/check-skill-upstreams.py --format json`，区分内容变化、引用漂移与正式发布 |

## 修改与验证顺序

1. `jj status`、`jj diff` 确认已有改动与本轮范围；普通只读任务不初始化仓库或安装工具。
2. 从当前任务、公共接口和用户例子确定验收行为，代码缺陷先补失败测试；文档和生成物不机械增加实现细节测试。
3. 修改中央源。新增资源后先执行 `python3 scripts/sync-packaged-source.py --apply`；该命令只依赖标准库，可在 editable 包尚未重建时运行。
4. 运行 `uv run --locked ruff check .`、`uv run --locked pytest -q`、`uv run --locked sync.py validate`。
5. 对本仓执行 `validate .`、`push . --dry-run`，检查范围后 `push . --apply`、`status --project .`。最终 apply 使用正式中央目录，不能让临时发布 clone 成为本仓长期来源记录。
6. 目录迁移先确认新输出、资源与调用策略，再按 [配置与迁移合同](../cli/configuration.md) 清理旧托管文件。保留用户自有文件，冲突时停止清理。
7. 内容源、CLI、模块是独立版本轴，同一轴的权威位置需一致。按功能领域拆分中文 jj change，提交与发布按当前任务授权执行。

## 内容边界

- 模板、模块清单、复制资源必须在约定来源边界内；模板在沙箱中渲染，不能调用任意 Python 能力。
- 内容源目录不接受目录符号链接；文件引用不能指向模块外，也不能显式引用 `.pyc` 等被清单忽略的文件。
- 镜像只包含 `agentphilosophy.content` 清单中的文件，拒绝符号链接，清除清单外残留；打包使用同一清单。
- `.DS_Store`、Python 缓存与本机元数据不参与内容指纹或分发。
- 当前 snapshot 审查不要求非空 diff；需要变更审查时使用当前任务、PR 或明确工作区基线，范围能确定时无需反复询问。

## 安装成本与兼容性

当前默认安装包含 `code-review-graph`，延续已有 CLI 对图谱命令的承诺。轻量安装已评估：单独提供 core/graph 组合需要新增分发与命令可用性合同，本次不通过隐式移除依赖来改变现有安装。按需选择 skill 的显式/隐式调用策略即可减少初始上下文；不为 Python 同步任务默认安装 Portless 或安全工具。
