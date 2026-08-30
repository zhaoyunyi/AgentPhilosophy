---
name: code-review-graph
description: 为 AgentPhilosophy 构建和查询 code-review-graph；适用于代码审查、改动影响范围、调用关系、测试缺口、架构探索、调试或安全重构，需要先用结构化图谱缩小源码读取范围时。
---

# Code Review Graph

本 skill 对接 [code-review-graph](https://github.com/tirth8205/code-review-graph) `2.3.8`。它负责告诉 agent 何时以及怎样使用图谱；真正的解析、存储和查询由 `code-review-graph` 依赖提供。

## 三层入口

- **Skill**：负责触发和编排工作流，不负责构建图谱，也不替代审查结论。
- **MCP**：MCP 是 agent 的主要查询接口。优先调用图谱工具取得最小上下文、影响半径、调用链、受影响流程和测试关系。
- **CLI**：负责安装 MCP、首次构建、增量更新、状态、watch、可视化和人工诊断。

在 Codex 中，上游 `install --platform codex` 会配置 MCP、hooks 和项目指令；上游不会为 Codex 生成原生 skill，本 skill 由 AgentPhilosophy 提供。

## 使用流程

1. 先判断当前会话是否已经提供 `code-review-graph` MCP tools。
2. MCP 可用时，先调用 `build_or_update_graph_tool` 更新图谱，再用 `get_minimal_context_tool` 缩小范围。
3. 代码审查优先调用 `detect_changes_tool`；需要执行路径时调用 `get_affected_flows_tool`；需要影响半径时调用 `get_impact_radius_tool`；需要测试关系时调用 `query_graph_tool(pattern="tests_for", ...)`。
4. 调试可查询 `callers_of`、`callees_of`、`importers_of` 或 `references_to`；架构探索使用 `get_architecture_overview_tool`。
5. 图谱用于缩小读取范围，不能替代读取实现与测试。对图谱选出的高风险源码、调用方和测试做实际检查后再下结论。
6. 空结果必须结合图谱是否已构建、是否落后于工作树和静态分析语言限制解释，不能直接等同于“没有影响”。

默认使用 `detail_level="minimal"`，证据不足时再扩大结果或切换为 `standard`，避免一次拉取过多上下文。

## CLI 引导与维护

配置 Codex 前先预览写入范围：

```bash
code-review-graph install --platform codex --repo . --dry-run
```

确认后安装，并在完成后重启 Codex：

```bash
code-review-graph install --platform codex --repo . --yes
code-review-graph build --repo .
code-review-graph status --repo .
```

常用维护命令：

```bash
code-review-graph update --repo .
code-review-graph watch --repo .
code-review-graph detect-changes --repo . --brief
code-review-graph visualize --repo .
```

在 AgentPhilosophy 源码仓中可使用 `uv run code-review-graph ...`。正式安装 AgentPhilosophy 后，包会重新导出同名 `code-review-graph` 命令。

## 写入与安全边界

- `install --platform codex` 会修改用户级 `~/.codex/config.toml`、`~/.codex/hooks.json`，并可能修改项目 `AGENTS.md` 与 Git hook；没有明确安装意图时只运行 `--dry-run`。
- `build`、`update`、`watch` 会在项目内维护 `.code-review-graph/` 数据；不要把本地图数据库当成业务源码或审查结论提交。
- 云端 embeddings 是显式可选能力；未获得授权时不配置 API key，不启用云端代码向量传输。
- 图谱是静态分析辅助证据。动态调用、反射、生成代码和框架约定可能不完整，最终结论仍以源码、测试和真实运行证据为准。
