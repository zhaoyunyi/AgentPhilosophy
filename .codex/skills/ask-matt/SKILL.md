---
name: ask-matt
description: 在当前工程 skill 家族中选择正确入口；适用于用户询问下一步该用哪个流程，或任务同时像需求、调研、原型、诊断、架构与实现时。
disable-model-invocation: true
---

# Ask Matt

改编自 Matt Pocock 的 `ask-matt` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/ask-matt

目标：只做路由，不代替被选择的 skill 执行工作。

## 主线

- 有代码库、想法仍模糊：`/grill-with-docs`。
- 无代码库的一般计划：`/grill-me`。
- 已讨论清楚且需要固化：`/to-spec`。
- spec 需要拆成可认领工作：`/to-tickets`。
- 单个明确 spec/ticket：`/implement`；内部按 `/tdd`，完成后 `/code-review`。

## 分流

- 难以靠讨论回答的交互、状态或界面问题：`/handoff -> /prototype -> /handoff`。
- 外部进入的 bug、需求或 PR 堆积：`/triage`；不要 triage `/to-tickets` 自己生成的票。
- 疑难 bug、偶发失败或性能回归：`/diagnosing-bugs`。
- 超过单个会话、路径仍被未知问题遮蔽：`/wayfinder`，清晰后回到 `/to-spec`。
- 需要一手资料证据：`/research`。
- 需要设计深模块、接口或 seam：`/codebase-design`。
- 需要扫描架构候选：`/improve-codebase-architecture`。
- merge、rebase 或 jj 冲突正在进行：`/resolving-merge-conflicts`。
- 需要跨会话保留上下文：`/handoff`。
- 需要长期教学工作区：`/teach`。
- 需要编写或审查 skill：`/writing-great-skills`。

首次使用工程流程但没有 `docs/agents/issue-tracker.md`、`docs/agents/domain.md` 时，先运行 `/setup-matt-pocock-skills`。

输出推荐的 skill、理由和紧接着的一步；如果信息不足，只问一个真正改变路由的问题。
