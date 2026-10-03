---
name: grill-me
description: 在 AgentPhilosophy 中对计划、决策或想法做一问一答的深入追问；适用于用户明确输入 /grill-me、要求 grill，或希望在行动前压实思路但不需要同步修改项目文档时。
disable-model-invocation: true
---

# Grill Me

改编自 Matt Pocock 的 `grill-me` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/grill-me

运行 `/grilling` 的一问一答流程，直到用户明确确认已经达成共享理解。

本入口不修改 `GLOSSARY.md` 或 ADR；需要在追问过程中同步沉淀领域语言和长期决策时，改用 `/grill-with-docs`。

不要在共享理解达成前实施方案，也不要把推荐答案当成用户决定。
