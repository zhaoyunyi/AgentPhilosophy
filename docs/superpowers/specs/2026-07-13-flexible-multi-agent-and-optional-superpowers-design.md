# 灵活多 Agent 约定与可选 Superpowers 设计

## 1. 背景

AgentPhilosophy 当前通过默认 preset 向下游项目同步两类协作约束：

- `model-constraints` 要求子任务默认继承当前会话模型和 reasoning。
- `superpowers-system` 默认写入 Superpowers 的安装路径、版本和排障规则。

这两个默认值限制了项目按任务选择模型和推理强度的空间，也让不需要 Superpowers 的项目承担了额外约束。本次调整要让下游项目在更新 AgentPhilosophy 后获得更灵活的多 Agent 规则，同时把 Superpowers 改为项目显式选择的可选模块。

## 2. 目标

1. `model-constraints` 继续作为所有默认 preset 的基础模块，并通过中央同步把新版多 Agent 规则传播到下游项目。
2. Agent 可以按任务复杂度、风险、不确定性、时效和成本选择合适的模型与推理强度。
3. 多 Agent 只用于可独立推进、职责和写入范围清晰的任务；子 Agent 必须获得明确目标、负责范围和验收结果。
4. `superpowers-system` 不再出现在默认 preset 和 AgentPhilosophy 自身的默认依赖中，但模块继续保留，供项目显式启用。
5. 版本与状态信号能够让下游项目识别本次中央内容和模块语义更新。

## 3. 非目标

- 不删除 `superpowers-system` 模块，也不改变显式启用该模块时的渲染内容。
- 不自动删除下游项目 `.agentphilosophy.yaml` 中已有的 `superpowers-system`。
- 不引入模型白名单、具体模型名、provider 约束或新的项目配置变量。
- 不在本次改动中推送主线、发布外部包或创建 GitHub Release。

## 4. 中央源与同步边界

### 4.1 多 Agent 规则

`modules/model-constraints` 是可维护中央源，`src/agentphilosophy/default_source/modules/model-constraints` 是随 Python 包分发的镜像。两处模板和模块元数据必须保持一致。

四个默认 preset 继续包含 `model-constraints`：

- `frontend`
- `fullstack`
- `mobile-sdk`
- `orchestrator`

因此，新项目初始化会直接获得新版规则；已有项目只要显式包含 `model-constraints`，在更新内容源后执行标准同步也会刷新 `AGENTS.md`。

### 4.2 Superpowers 可选模块

四个默认 preset 和当前仓 `.agentphilosophy.yaml` 移除 `superpowers-system`。包内 preset 镜像必须同步移除。

`modules/superpowers-system`、包内模块镜像和 catalog 条目继续保留。下游项目已经显式声明该模块时，后续同步仍正常渲染 Superpowers 规则；中央同步不替项目撤销已有的显式选择。

### 4.3 当前仓托管输出

AgentPhilosophy 自身配置移除 `superpowers-system` 后，通过同步器刷新托管的 `AGENTS.md`，使当前仓与默认策略一致。不得直接只删生成文案而保留配置依赖。

## 5. 多 Agent 行为规则

新版规则采用能力与任务匹配语义，不规定具体模型名称：

- 根据任务复杂度、风险、不确定性、时效和成本选择合适的模型与推理强度。
- 高风险、跨模块、难验证或证据不足的任务使用能力更强的模型与更充分的推理。
- 机械、低风险、边界清晰且容易验证的任务可以使用更轻量的模型与推理强度。
- 只有任务能够独立推进、职责清晰且写入范围不冲突时才使用多 Agent。
- 为子 Agent 明确目标、负责范围、输入、预期产物和验收标准；修改代码时避免覆盖其他 Agent 或用户的改动。

规则不再要求子任务默认继承当前会话模型和 reasoning，也不使用“不得指定更弱模型”这类单向约束。

## 6. LLM 接入协议

CLI 与 LLM 使用文档必须反映新的默认值：

- 自动配置模式不得为默认 preset 自动追加 `superpowers-system`。
- 用户断点模式将 Superpowers 描述为显式可选模块，推荐项改为默认不追加。
- 完整 CLI 文档的示例默认模块列表不包含 `superpowers-system`，并说明需要时如何显式追加和验证。
- README 与文档索引保持可发现性，不再把 Superpowers 描述为默认 preset 约束。

## 7. 版本策略

本次变更按 `0.7.7` 本地 release 准备：

- CLI 版本：`0.7.7`。
- 中央内容版本：`0.7.7`。
- `model-constraints` 模块版本：`1.1.0`。
- `superpowers-system` 模块版本保持 `6.1.1`，因为其显式启用后的模块语义未变化。

CLI 与内容版本使依赖项目看到整体 stale 信号；模块版本使包含 `model-constraints` 的项目看到具体模块 stale 信号。

## 8. 兼容与失败处理

- 新项目：默认配置不包含 Superpowers，同步后的 `AGENTS.md` 不出现空白 Superpowers 区块。
- 旧项目显式启用 Superpowers：保持配置和渲染结果，不自动移除。
- 旧项目未启用 Superpowers：升级不会新增该模块。
- 配置或托管输出存在漂移：继续使用 `validate`、`push --dry-run` 和 `push --apply` 的现有冲突保护，不绕过 state 手工覆盖。
- 中央源与包内镜像不一致：验证必须失败，禁止把不一致的默认源打包发布。

## 9. BDD 与验证

### 9.1 用户行为场景

场景一：默认 preset 获得新版多 Agent 规则。

- Given 使用任一默认 preset 初始化项目。
- When 执行 `push --apply`。
- Then `.agentphilosophy.yaml` 包含 `model-constraints`、不包含 `superpowers-system`，且 `AGENTS.md` 包含灵活选择模型与推理强度的规则。

场景二：项目显式选择 Superpowers。

- Given 项目在 `.agentphilosophy.yaml` 显式声明 `superpowers-system`。
- When 执行 `push --apply`。
- Then `AGENTS.md` 仍完整包含 Superpowers 的版本、路径和排障规则。

场景三：默认配置不产生空白章节。

- Given 默认 preset 未启用 `superpowers-system`。
- When 渲染 `AGENTS.md`。
- Then 工程规范前不存在多余空白区块或空的 Superpowers 标题。

### 9.2 验证命令

实现完成后运行最新结果：

```bash
uv run sync.py validate
uv run ruff check .
uv run pytest -q
uv lock --check
uv build
bash scripts/release-smoke.sh
uv run sync.py status --project .
```

## 10. 完成标准

- 根目录中央源与包内默认源内容一致。
- 四个默认 preset 不再包含 `superpowers-system`，但仍包含 `model-constraints`。
- 默认同步结果包含新版多 Agent 约定，不包含 Superpowers 规则。
- 显式启用 Superpowers 的兼容路径通过测试。
- AgentPhilosophy 当前仓配置和托管输出符合新默认策略。
- `0.7.7` 版本、release notes、测试与安装后 smoke 在本地通过；不执行外部发布。
