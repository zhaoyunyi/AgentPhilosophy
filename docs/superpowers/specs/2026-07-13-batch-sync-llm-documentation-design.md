# 批量同步后调用大模型更新项目文档设计

## 1. 背景

AgentPhilosophy 已支持通过 `registry.yaml` 和 `push --all --apply` 批量刷新依赖项目的托管输出，并把 CLI、中央内容源和模块版本写入各项目的 `.agents/agentphilosophy-state.yaml`。当前缺口是：托管规则更新后，项目自有的 README、架构说明和运维文档不会自动跟随新规则审查与更新。

## 2. 目标

1. 复用 `push --all --apply`，在每个项目同步成功后按需调用外部大模型 CLI 更新项目自有文档。
2. 只为本轮确实发生版本、模块或托管输出变化的项目调用模型；已经最新的项目不重复消耗模型资源。
3. 每个依赖项目在 `registry.yaml` 显式声明允许更新的文档路径。
4. 模型命令由调用方显式传入，通过标准输入接收中文任务提示，不绑定具体供应商、账号或模型。
5. 模型执行后复查 AgentPhilosophy 托管文件、项目配置和 state；若模型改动这些保护文件，命令必须失败并报告漂移。
6. 只有文档阶段成功后才把当前版本、内容源、模块和源树指纹记录为已刷新；失败后修复原因并重跑时不得因同步版本已经更新而跳过。

## 3. 非目标

- 不在 `.agentphilosophy.yaml` 中保存本机模型命令、账号或密钥。
- 不自动提交、推送或发布依赖项目的文档改动。
- 不替模型判断任意仓库中的所有文档范围；未声明 `documentation_paths` 的项目只执行同步并跳过模型。
- 不绕过现有 `validate`、冲突检测、dry-run 或 state 管理规则。

## 4. CLI 合同

批量应用同步并更新文档：

```bash
agentphilosophy-sync push --all --apply \
  --project-name ExampleFullstack \
  --update-docs \
  --llm-command 'codex exec --ephemeral --sandbox workspace-write -'
```

可用 `--llm-timeout <秒>` 设置单个项目的模型执行超时，默认 900 秒。

安全约束：

- `--update-docs` 只能和 `--all --apply` 一起使用。
- `--update-docs` 必须同时提供非空 `--llm-command`。
- `--llm-command` 使用参数解析后直接执行，不经过 shell。
- `--project-name` 可重复提供，只处理 registry 中名称完全匹配的项目；省略时处理全部项目。
- 单个项目同步失败时，不为该项目调用模型；其他 registry 项目继续处理。
- 模型成功后在 state 中记录包含 `documentation_paths` 的 `documentation_refresh` 指纹；失败、超时、配置错误、托管文件漂移、保护文件漂移或白名单外改动时不记录，允许后续重试。

## 5. Registry 合同

```yaml
schema_version: 1
projects:
  - name: ExampleFullstack
    path: /absolute/path/to/ExampleFullstack
    documentation_paths:
      - README.md
      - docs
```

`documentation_paths` 是相对项目根目录的文件或目录列表。绝对路径、越过项目根目录的路径、保护区、空列表和错误类型必须拒绝，不允许扩大模型写入范围。模型执行后必须用前后快照校验实际变更；只靠提示词约束不构成成功条件。

## 6. 更新判断与提示词

模型调用前记录旧 state，并检查以下任一变化：

- CLI 版本变化；
- 中央内容版本变化；
- 已选择模块的版本变化；
- 同步计划包含 `add` 或 `update`。

提示词至少包含：项目名、版本变化、更新的托管输出、允许修改的文档路径、当前托管文件清单和以下行为边界：

- 先读取项目内 `AGENTS.md`、`CLAUDE.md`、README 和相关索引；
- 只修改 `documentation_paths` 内的项目自有文档；
- 不修改 `.agentphilosophy.yaml`、`.agents/`、skills 或任何托管文件；
- 让文档描述与同步后的当前实现和验证命令一致，并同步维护文档索引；
- 不提交、不推送、不发布。

## 7. BDD 场景

### 场景一：批量同步后更新项目文档

- Given registry 项目已同步旧版 AgentPhilosophy，并声明了文档路径。
- When 中央内容升级后执行 `push --all --apply --update-docs --llm-command ...`。
- Then 托管输出和 state 先更新到新版本，模型随后收到版本、托管输出和文档范围提示，并更新允许范围内的项目文档。

### 场景二：模型改动托管文件时失败

- Given 项目同步成功并调用模型。
- When 模型修改了 AgentPhilosophy 托管文件。
- Then CLI 返回失败，明确列出发生漂移的托管文件，要求人工审查；不把漂移写回 state。

### 场景三：项目已经最新时跳过模型

- Given 项目的 CLI、内容源、模块和托管输出都已是当前版本。
- When 再次执行同一批量命令。
- Then 不调用模型，并报告项目已是最新。

### 场景四：同步冲突时不调用模型

- Given 项目存在手工修改的托管文件。
- When 执行批量同步和文档更新。
- Then 现有冲突保护使该项目同步失败，模型不执行。

### 场景五：模型阶段失败后可以重试

- Given 项目同步成功，但文档路径配置错误或模型命令失败。
- When 修复原因后再次执行同一批量命令。
- Then 即使同步版本已经是当前版本，模型阶段仍会再次执行；仅在成功后记录刷新指纹。

### 场景六：单项目失败不阻断后续项目

- Given registry 中第一个项目的文档配置无效，后续项目配置有效。
- When 执行批量同步和文档更新。
- Then 命令汇总失败，但仍为后续项目执行文档更新并分别报告结果。

### 场景七：扩大文档范围后重新刷新

- Given 项目已经完成当前版本文档刷新。
- When registry 为该项目新增允许文档路径并再次执行。
- Then 文档路径指纹发生变化，模型重新执行并在成功后写入新指纹。

## 8. 完成标准

- 成功路径和关键失败路径具有行为级 BDD 覆盖。
- 旧的 `push --all --dry-run` 与 `push --all --apply` 行为保持兼容。
- 未显式启用 `--update-docs` 时不启动任何外部进程。
- 完整测试、lint、中央源校验与打包源镜像检查通过。

## 9. 版本策略

- CLI 版本与中央内容版本统一提升到 `0.7.8`，使依赖项目同时获得 CLI stale 和内容 stale 信号。
- 本轮允许按功能领域提交并推送 `main`，但稳定安装命令仍指向已发布的 `v0.7.7`；不打 `v0.7.8` tag，不创建 GitHub Release。
