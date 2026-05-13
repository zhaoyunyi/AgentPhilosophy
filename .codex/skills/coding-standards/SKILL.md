---
name: coding-standards
description: AgentPhilosophy 的编码、测试、review 和验证收口规则。
---

# coding standards

- 新功能和 bugfix 默认先写失败测试。
- 代码实现优先复用现有模式，不引入无必要抽象。
- 完成前运行 `uv run pytest -q` 并记录结果。
