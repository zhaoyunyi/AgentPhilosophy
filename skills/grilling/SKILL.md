---
name: grilling
description: 在 AgentPhilosophy 中对计划或设计做 relentless interview；适用于用户要求 grill、澄清需求、压实方案、避免直接开工，或 /grill-with-docs 需要底层一问一答流程时。
---

# Grilling

改编自 Matt Pocock 的 `grilling` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/grilling

目标：沿设计树逐步追问，直到你和用户达成共享理解。

## 流程

1. 先用一句话复述当前计划目标。
2. 找出最高风险的未知点：用户价值、边界、失败路径、状态变化、权限、数据、发布和验收。
3. 每次只问一个问题，并附上推荐答案。
4. 如果问题能通过代码、文档、配置或日志回答，先查现场事实。
5. 等用户回答后再进入下一问；不要批量问卷。
6. 所有关键分支都清楚后，总结已确定内容、未做范围和推荐下一步。

## 禁止

- 不在用户确认“已经达成共享理解”前实施方案。
- 不把未确认的推荐答案写成事实。
- 不用泛泛的“还有补充吗”代替具体追问。
