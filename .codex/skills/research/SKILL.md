---
name: research
description: 针对高可信一手来源调研问题并把带引用结论写成项目内 Markdown；适用于资料、API、标准、论文或外部事实需要证据化核实时。
---

# Research

改编自 Matt Pocock 的 `research` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/research

1. 明确研究问题、可信来源标准、时间边界和产物路径。
2. 联网时遵守当前环境的网络访问 skill；技术事实优先官方文档、源码、规范和论文。
3. 任务足够独立且当前环境允许时，交给后台 agent 调研；否则在当前会话完成。后台任务必须写清目标、范围、产物和验收标准。
4. 把结果保存为项目拥有的带引用 Markdown。默认写入现有研究目录；没有约定时建议 `docs/research/<topic>.md` 并先确认长期文档入口。
5. 区分已验证事实、来源推断、分歧和未解决问题；引用紧跟对应结论。
6. 新增长期文档时同步更新 `docs/README.md` 或项目实际索引。

研究只提供决策输入，不替用户做产品选择，也不直接进入实现；通常把结果交给 `/grill-with-docs` 或 `/to-spec`。
