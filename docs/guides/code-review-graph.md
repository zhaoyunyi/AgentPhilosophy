# code-review-graph 使用指南

AgentPhilosophy 从 v0.8.0 起固定依赖 [`code-review-graph`](https://github.com/tirth8205/code-review-graph) `2.3.8`，并重新导出同名 `code-review-graph` 命令。默认 preset 同时包含 `skill-code-review-graph`，把使用规则同步到仓库级 `skills/code-review-graph/` 和 Codex 项目级 `.codex/skills/code-review-graph/`。

## 到底使用 Skill、CLI 还是 MCP

三者都会用，但职责不同：

| 入口 | 用途 | 是否直接分析图谱 |
| --- | --- | --- |
| Skill | 让 agent 在审查、影响分析、调试、架构探索和安全重构时主动进入图谱工作流 | 否，只负责触发和编排 |
| MCP | agent 日常查询图谱的主要入口，返回最小上下文、改动风险、影响半径、调用关系、流程和测试关系 | 是 |
| CLI | 安装 MCP、首次构建、增量更新、状态、watch、可视化和人工诊断 | 是 |

因此，日常让 Codex 审查代码时，推荐路径是：**Skill 触发 → MCP 查询 → agent 阅读图谱选中的源码和测试**。CLI 主要负责初始化和维护；MCP 不可用时，CLI 也可以作为人工或自动化兜底。

上游 `2.3.8` 的 Codex 安装器会注册 MCP、安装 hooks 并向 `AGENTS.md` 注入图谱使用指令，但不会生成 Codex 原生 skill。AgentPhilosophy 的 `skill-code-review-graph` 补上了项目级 skill discovery 入口。

## 安装与配置 Codex

先预览上游安装器会修改什么：

```bash
code-review-graph install --platform codex --repo . --dry-run
```

确认后安装：

```bash
code-review-graph install --platform codex --repo . --yes
```

该命令会修改用户级 `~/.codex/config.toml`、`~/.codex/hooks.json`，并可能修改当前项目的 `AGENTS.md` 与 Git hook。安装完成后重启 Codex，让 MCP 配置生效。

如果只想先验证 CLI 和图谱，不准备修改 Codex 配置，可以跳过 `install`，直接构建：

```bash
code-review-graph build --repo .
code-review-graph status --repo .
```

在 AgentPhilosophy 源码仓中也可以显式通过 uv 环境运行：

```bash
uv run code-review-graph --version
uv run code-review-graph build --repo .
```

## Codex 中的推荐工作流

### 审查当前改动

向 Codex 提出正常的审查请求即可，例如：

```text
审查当前未提交改动，先用 code-review-graph 识别影响范围和测试缺口，再按 Standards 与 Spec 输出 findings。
```

agent 应优先调用：

1. `build_or_update_graph_tool`：把图谱同步到当前工作树。
2. `get_minimal_context_tool`：获取当前任务所需的最小结构上下文。
3. `detect_changes_tool`：分析改动函数、风险、受影响流程和测试缺口。
4. `get_affected_flows_tool` / `get_impact_radius_tool`：在需要时补充执行路径和爆炸半径。
5. `query_graph_tool(pattern="tests_for", ...)`：核对高风险函数的测试关系。

图谱只负责缩小范围，agent 仍必须读取被选中的源码、调用方和测试，不能仅凭图谱元数据给出审查结论。

### 调试或理解调用关系

可以直接描述目标：

```text
用 code-review-graph 找出这个函数的调用方、被调用函数、导入方和受影响流程，再结合源码诊断根因。
```

常见查询包括 `callers_of`、`callees_of`、`importers_of`、`references_to` 和 `tests_for`。

### 理解架构

```text
用 code-review-graph 给出当前项目的架构社区、跨社区耦合和关键桥接节点，并回读对应源码验证。
```

agent 可使用 `get_architecture_overview_tool`、`get_hub_nodes_tool` 和 `get_bridge_nodes_tool`。

## CLI 常用命令

```bash
code-review-graph build --repo .
code-review-graph update --repo .
code-review-graph status --repo .
code-review-graph watch --repo .
code-review-graph detect-changes --repo . --brief
code-review-graph visualize --repo .
code-review-graph uninstall --repo . --dry-run
```

- `build`：首次全量构建。
- `update`：增量更新。
- `watch`：监听文件变化并自动更新。
- `detect-changes --brief`：在终端查看风险摘要。
- `visualize`：生成交互式 HTML 图谱。
- `uninstall --dry-run`：先预览卸载范围，不直接删除配置。

## 数据与安全边界

- 默认图谱和源码解析在本地完成，数据写入项目 `.code-review-graph/`。
- 云端 embeddings 是可选能力。没有明确授权时，不配置云端 API key，也不启用代码向量传输。
- `.code-review-graph/` 是派生数据，不是业务源码，也不是正式审查回执。
- 静态图谱无法完整覆盖动态调用、反射、生成代码和部分框架约定；空结果不代表确定没有影响。
- 在 jj colocated git 仓库中仍可使用，因为底层 Git 工作树可供上游识别；版本控制操作继续遵循项目 jj 规范。
