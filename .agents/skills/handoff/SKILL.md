---
name: handoff
description: 把当前会话压缩成可供新会话或另一个 agent 接续的交接文档。
disable-model-invocation: true
---

# Handoff

改编自 Matt Pocock 的 `handoff` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/handoff

把交接文档写入操作系统临时目录，不写入当前工作区，除非用户明确要求长期保存。

交接文档包含：

- 目标、范围和用户原话中的关键约束。
- 已验证事实、已经做出的决策和对应证据。
- 已完成工作、当前工作区状态和修改文件。
- 已运行验证及结果。
- 剩余工作、阻塞项、风险和明确非目标。
- 建议新会话调用的 skills。
- 新会话第一条可执行动作。

已有 spec、ADR、issue、提交、diff 或报告只写路径/URL，不复制正文。完成后返回绝对路径，并说明新会话如何引用它。
