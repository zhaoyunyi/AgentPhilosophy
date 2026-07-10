# AgentPhilosophy 0.7.5 与 cadraq 同步设计

## 背景

AgentPhilosophy 已发布版本为 `0.7.4`，中央仓当前还有一组尚未发布的默认协作、DDD 与产品文案模板更新。cadraq 当前通过 `.agentphilosophy.yaml` 关联本地中央源 `/Users/zhaoyunyi/developer/AgentPhilosophy`，同步状态仍记录为 `0.7.0`。

本轮先把中央工作区更新整理为 AgentPhilosophy `0.7.5` 并完成发布，再让 cadraq 从已发布的中央源同步。cadraq 的模块集合已经与 `orchestrator` 默认 preset 对齐，不额外启用可选模块。

## 目标

1. 将中央仓当前模板更新连同必要的兼容扩展发布为 `0.7.5`。
2. 保证根目录中央源与 packaged default source 内容一致。
3. 让 cadraq 同步默认 preset 中现有 skill 的最新输出，包括 `to-spec`、`to-tickets` 和更新后的 Portless skill。
4. 保留 cadraq 的验证边界入口，不用强制覆盖或遗留托管漂移。
5. 用发布 smoke、目标仓 contract 与 AgentPhilosophy status 证明同步闭环完成。

## 非目标

- 不把 `skill-philosophy-extraction`、独立 `skill-code-review` 等可选模块加入 cadraq。
- 不修改 cadraq 的业务功能、用户流程或部署行为。
- 不顺手升级与本轮模板或 preset 输出无关的外部 skill 上游。
- 不手工编辑 `.agents/agentphilosophy-state.yaml`。

## 方案

### 1. 中央模板与版本发布

保留并验证当前工作区中的 `doc-templates`、`spec-ddd`、`spec-product-copy` 更新。为 `spec-test-general` 增加可选的验证指南路径变量：未配置时继续生成当前通用测试策略；配置时追加“验证边界”章节和项目指南链接。

该扩展使项目特有入口由 `.agentphilosophy.yaml` 的变量驱动，输出仍由中央模板托管，避免 cadraq 直接修改 `managed_replace` 文件后持续产生冲突。对应模块版本、packaged source 和测试必须同步更新。

中央内容完成后使用仓库发布脚本准备 `0.7.5`，统一 CLI version 与 content version。发布 change 通过完整验证后移动 `main` bookmark、推送远端，并创建 GitHub Release `v0.7.5`。

### 2. cadraq preset 与依赖关联

cadraq 保持 `preset: orchestrator` 和本地 `source` 路径。其模块集合已经与当前 `orchestrator` 默认 preset 一致，因此不机械重写模块列表；只增加验证指南路径变量，并由 `push --apply` 更新托管输出和 state。

`skill-mattpocock-engineering` 在新版本中继续提供兼容别名 `to-prd`、`to-issues`，同时新增主线输出 `to-spec`、`to-tickets`。`skill-portless-local-dev` 已属于默认 preset，本轮刷新其最新内容，不重复增加模块。

### 3. 数据流

1. AgentPhilosophy 根目录模块与模板是开发事实源。
2. packaged default source 是发布包内镜像，必须与根目录事实源一致。
3. `prepare-release.sh` 生成 `0.7.5` 构建产物并执行安装后 smoke。
4. GitHub Release 发布完成后，cadraq 通过本地中央源执行 `validate`、`push --dry-run`、`push --apply`。
5. 同步器根据 `.agentphilosophy.yaml` 渲染 repo skill、Codex skill、规范文档和 state。
6. `status --project`、skill discovery 与 cadraq contract test 验证最终状态。

## 冲突与失败处理

- 中央测试或 release smoke 失败时停止发布，不移动 `main`，不创建 Release。
- 远端 `main` 与本地发布 change 不一致时停止发布，先复核 bookmark 与远端状态。
- cadraq dry-run 出现除已识别 `spec/TestStrategy.md` 之外的新冲突时停止 apply，逐项确认来源。
- 验证指南扩展落地后，`spec/TestStrategy.md` 应由模板完整生成；不通过手改 state、强制覆盖后再手改、或忽略冲突收口。
- cadraq 验证失败时保留中央发布结果，但不把目标仓同步声明为完成。

## 验证

### AgentPhilosophy

- `uv run ruff check .`
- `uv run pytest -q`
- `uv run sync.py validate`
- `bash scripts/prepare-release.sh 0.7.5`
- 构建产物安装后 smoke
- 发布后复核 GitHub Release、tag、`main` 与 `main@origin`

### cadraq

- `uv run sync.py validate /Users/zhaoyunyi/developer/cadraq`
- `uv run sync.py push /Users/zhaoyunyi/developer/cadraq --dry-run`
- `uv run sync.py push /Users/zhaoyunyi/developer/cadraq --apply`
- `uv run sync.py status --project /Users/zhaoyunyi/developer/cadraq`
- `find -L .codex/skills -name SKILL.md`
- 运行覆盖 `spec/TestStrategy.md` 验证指南入口的 contract test
- 按 cadraq 验证边界补跑配置、格式、类型、lint 或 OpenSpec 检查，以实际 diff 决定最小完整集合

## 完成标准

- AgentPhilosophy `v0.7.5` 已在远端发布，构建产物和 release smoke 通过。
- cadraq state 记录 `agentphilosophy_version: 0.7.5` 与 `source_content_version: 0.7.5`。
- cadraq 的 repo skill 与 `.codex/skills` 同时存在 `to-spec`、`to-tickets`，并完成 Portless 等更新。
- `spec/TestStrategy.md` 保留验证指南入口且不再报告托管漂移。
- `status --project` 无 stale 或 conflict，目标仓相关验证通过。
