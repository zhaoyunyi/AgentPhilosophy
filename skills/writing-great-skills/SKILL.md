---
name: writing-great-skills
description: 编写、重构或审查可预测、可组合且上下文成本合理的 Agent Skill；适用于 skill 触发、步骤、参考资料与渐进披露设计。
disable-model-invocation: true
---

# Writing Great Skills

改编自 Matt Pocock 的 `writing-great-skills` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/writing-great-skills

根本目标是流程可预测：同类输入每次走相同的可靠过程，而不是产生完全相同的文字。

## 调用方式

- 模型需要自动发现或其他 skill 需要调用时，保留丰富、面向模型的 `description`。
- 只有用户明确输入才应启动时，设置 `disable-model-invocation: true`，避免永久上下文负担。
- `agents/openai.yaml` 的 implicit policy 应与 frontmatter 语义一致。

## 信息层级

1. 所有分支都必须立即知道的动作放在 `SKILL.md`。
2. 条件分支需要的步骤放到链接文件，指针必须写清何时读取。
3. 多步骤共享的术语和规范放参考文件。
4. 工具帮助、外部文档和项目事实保持在来源处，不复制成易过期正文。

每个步骤都应有可检查的完成条件。把未来步骤展示得太早会诱发提前结束；先锐化当前完成条件，仍不稳定时再拆分上下文。

## 编写与审查

1. 从真实失败模式和触发语句开始，而不是从工具清单开始。
2. 选择一个模型已有强语义的 leading word，统一描述与正文词汇。
3. 删除不改变模型行为的 no-op、重复规则、过期 sediment 和无法验收的措辞。
4. 用正向目标描述期望行为；硬性禁止同时给出正确替代动作。
5. 对每个分支模拟一次完整运行，检查触发、读取路径、完成标准、写入边界和失败恢复。
6. 在项目中新增或修改 skill 时遵守中央源、packaged mirror、索引和测试合同。

完整术语见 [GLOSSARY.md](GLOSSARY.md)。
