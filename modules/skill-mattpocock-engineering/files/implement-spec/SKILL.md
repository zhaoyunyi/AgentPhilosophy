---
name: implement-spec
description: 实现 /to-spec 和 /to-tickets 形成的整份 spec；适用于用户输入 /implement-spec、要求按依赖图完成所有 tickets，或明确要求在一个集成分支上编排实现与验收。
disable-model-invocation: true
---

# Implement Spec

改编自 Matt Pocock 的 `implement-spec` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/implement-spec

目标：把 tickets 视为带阻塞关系的任务图，在单一集成分支或 jj change 链上完成整份 spec。单票实现使用 `/implement`。

## 执行前

1. 读取 spec、tickets、`AGENTS.md`、`GLOSSARY.md`、相关 ADR 和测试策略。核对范围、验收条件、阻塞边和完成标准。
2. 从项目 `docs/agents/issue-tracker.md` 确认 tracker 及关闭工作的方法。未配置时停止，并请用户先运行 `/setup-matt-pocock-skills`。
3. 列出已完成、可执行和受阻的 tickets；仅当所有阻塞项已满足时，ticket 才进入可执行集合。依赖循环、缺失 ticket 或无法核实的阻塞项必须报告，不能标成完成。
4. 优先使用项目版本控制约定。jj 项目使用隔离 workspace 和 change；需要分支时使用 `codex/` 前缀。不要重置、覆盖用户或其他 agent 的工作。

## 实现循环

1. 建立集成分支或 change 链，记录起点。沟通以 spec、ticket、资料和 change 的上下文指针为主，不重复复制全文。
2. 需要调研时先做只读探索；使用探索子 agent 时，把结论保存在项目允许的目录并提供指针。
3. 只为可独立推进、写入范围不冲突的 tickets 启动实现子 agent；明确目标、输入、负责文件、产物和验收命令。每个实现者使用独立 workspace，以当前集成结果为起点，按 `/tdd` 验证行为。
4. 由单一集成 owner 串行合入完成的结果，核对验收证据并运行集成检查。冲突按双方意图解决；合入与验证成功后才解除后续 tickets 的阻塞。
5. 工具不支持子 agent 或并行会造成写入冲突时，按依赖顺序自行执行，保持相同验收标准。
6. 所有 tickets 完成后，对集成结果运行 `/code-review`，核对 Standards 与 Spec，修复发现并重新验证。

## 完成条件

- 每个 ticket 的验收标准都有最新证据，整份 spec 的验证通过。
- 用户要求 PR，或已授权的 tracker 流程以 PR 收尾时，首个集成结果产生后创建 Draft PR，并用 `/pr` 组织正文；最终验证通过后按该流程移交 review。
- tracker 写入和向他人发送消息遵循当前授权；未完成的外部写入如实报告，不宣称 ticket 已关闭。
- 报告集成结果、验证、未完成项和外部回执；清理本轮创建且不再需要的 workspace，保留可恢复结果。
