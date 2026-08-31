---
name: writing-for-agents
description: 编写或修改供 Agent 使用的文档；适用于 Skills、AGENTS.md、CLAUDE.md 以及由它们指向的长期说明。
---

# Writing for Agents

改编自 Matt Pocock 的 `writing-for-agents` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/writing-for-agents

目标是让同类输入稳定走过同一可靠过程。Skill 特有的 frontmatter、调用方式和路由规则见 [SKILL-MECHANICS.md](SKILL-MECHANICS.md)。

## 编写原则

- **上下文指针**同时写清材料是什么、什么分支需要读取；触发条件比目标路径更影响可靠性。
- **信息层级**按即时步骤、文件内参考、按需披露的外部参考排列。所有分支都需要的内容留在主文件，条件分支才下沉。
- 每个步骤用可检查且足够完整的**完成条件**抵抗提前结束。
- 使用模型已有语义的 **leading word** 稳定触发和执行，避免用多句同义解释重复一个概念。
- 同一规则只保留一个真值；配置、目录和 `--help` 已能便宜查到的事实不复制成容易过期的 **cache**。
- 删除不改变行为的 no-op、重复内容和已失效的 sediment；优先用正向目标描述应该做什么。
- 概念的定义、规则和例外放在一起，避免把一个含义分散在多个章节。

## 完成检查

1. 每个入口能从描述判断何时触发、何时不触发。
2. 每个步骤有完成条件，条件分支只加载必要材料。
3. 文件、配置和代码之间没有重复真值或旧名称。
4. 修改 skill 时同步维护中央源、包内镜像、索引、双目标输出与行为测试。
