---
name: to-spec
description: 把 AgentPhilosophy 当前已澄清的对话、方案或 /grill-with-docs 结果整理成 spec；适用于用户输入 /to-spec、要求从上下文生成产品/工程规格，或需要先把方案固化再拆 tickets。
---

# To Spec

改编自 Matt Pocock 的 `to-spec` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/to-spec

目标：把已经讨论清楚的内容整理成可交给实现 agent 的 spec，不重新访谈用户。

## 流程

1. 读取当前对话、相关代码和文档，使用 `CONTEXT.md` 的领域词，尊重相关 ADR。
2. 明确测试 seam：优先选最高、最稳定、最接近用户行为的 seam。需要新增 seam 时先说明理由，并和用户确认。
3. 生成 spec。优先读取 `docs/agents/issue-tracker.md` 并按其中合同发布；否则沿用项目已有 spec/PRD 目录。仍无约定时先给出建议路径并询问确认，不擅自创建公开 issue。
4. spec 完成后建议下一步运行 `/to-tickets`。

## Spec 模板

```markdown
# <功能或问题名> Spec

## Problem Statement

从用户视角描述问题。

## Solution

从用户视角描述解决方案。

## User Stories

1. As a <actor>, I want <capability>, so that <benefit>.

## Implementation Decisions

- 已确认的模块、接口、数据、状态、权限、迁移、发布或架构决策。
- 不写易过期的文件路径或代码片段；只有原型产出的状态机、schema 或类型形状比 prose 更精确时才摘录关键片段。

## Testing Decisions

- 测试 seam。
- 用户可见行为和关键失败路径。
- 可复用的既有测试模式。

## Out of Scope

- 明确不做的事项。

## Further Notes

- 风险、开放问题、迁移或发布注意事项。
```

## 禁止

- 不把新的需求访谈混进 `/to-spec`；信息不足时标明缺口并返回 `/grill-with-docs`。
- 不写“应该会”“可能可以”这种无法验收的措辞。
- 不把 spec 变成实现 checklist；spec 描述产品行为、约束和验收。
