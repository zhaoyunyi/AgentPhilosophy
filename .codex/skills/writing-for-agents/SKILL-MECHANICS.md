# Skill 调用与结构

## 调用方式

- **模型可调用**：保留面向模型的 `description`，不设置 `disable-model-invocation`，`agents/openai.yaml` 不禁止 implicit invocation。适用于 agent 必须主动发现，或其他流程必须能触发的能力。
- **仅用户调用**：设置 `disable-model-invocation: true`，并在 OpenAI metadata 中设置 `allow_implicit_invocation: false`。description 只需帮助人识别用途。

模型可调用会持续消耗少量上下文；仅用户调用把索引责任交给用户。只有确实需要主动触发时才支付前者成本。

## 按调用拆分

一个分支有独立触发词、必须被主动发现，或被多个流程共享时，可以拆成单独的模型可调用 skill。只被一个流程按条件读取的参考资料，优先保留为普通链接文件。

当仅用户调用的 skill 多到难以记忆时，用一个仅用户调用的 router skill 列出入口和选择条件；router 负责推荐，不冒充被选 skill 执行工作。
