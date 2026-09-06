# Skill 设计术语

- **Predictability**：每次运行遵循相同可靠过程，而非输出相同内容。
- **Model-invoked**：模型可自动发现，也可由用户调用；description 带来持续上下文成本。
- **User-invoked**：只有用户明确调用；降低上下文成本，但增加人的记忆成本。
- **Context pointer**：说明何时读取外部材料的指针；可靠性取决于措辞而不只取决于路径。
- **Information hierarchy**：从 `SKILL.md` 当下步骤、条件步骤、参考文件到外部来源的分层。
- **Progressive disclosure**：只在分支需要时加载后续材料。
- **Leading word**：借用模型已有语义、稳定触发和执行的核心词。
- **Completion criterion**：可判断当前步骤真正完成的条件。
- **Premature completion**：当前步骤边界含糊，被后续步骤吸引而过早结束。
- **Legwork**：agent 在步骤内部自己完成的查找、验证和整理工作。
- **Sediment**：不再服务当前能力却仍残留的历史内容。
- **Duplication**：同一规则在多处维护，产生漂移风险。
- **No-op**：没有改变模型默认行为、却持续消耗上下文的指令。

审查 skill 时，用这些术语定位问题，并给出删除、内联、下沉、拆分或强化完成条件的具体修改。
