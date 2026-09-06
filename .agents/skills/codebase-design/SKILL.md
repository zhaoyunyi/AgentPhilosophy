---
name: codebase-design
description: 设计深模块、接口和 seam；适用于模块接口、架构加深、可测试性、适配器边界或 agent 可导航性问题。
---

# Codebase Design

改编自 Matt Pocock 的 `codebase-design` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/codebase-design

目标：让大量行为藏在小接口后，通过清晰 seam 提供调用方杠杆、维护局部性和稳定测试面。

## 统一语言

- **Module**：拥有 Interface 与 Implementation 的任意尺度单元。
- **Interface**：调用方正确使用模块必须知道的全部事实，包括不变量、错误、顺序和性能。
- **Implementation**：模块内部行为。
- **Depth**：每单位 Interface 可获得的行为与能力。
- **Seam**：无需在调用处修改代码即可替换行为的位置。
- **Adapter**：在 seam 上满足 Interface 的具体角色。
- **Leverage**：一个实现对多个调用方和测试的复用价值。
- **Locality**：变化、知识和验证集中在一个地方。

## 设计规则

1. 先画出当前调用者、依赖、行为和失败路径，判断复杂度是否散落。
2. 用删除测试判断模块价值：删除后复杂度若重新散回多个调用者，模块正在提供深度；若复杂度消失，它可能只是透传层。
3. Interface 同时是调用面和测试面；测试需要绕过接口通常说明 seam 放错。
4. 一个 adapter 时不要为想象中的变化制造 seam；至少两个真实替代物才证明 seam 的价值。
5. 接受依赖并返回结果，让副作用留在适配器边界。
6. 深化一组依赖时读取 [DEEPENING.md](DEEPENING.md)；存在多个合理接口方向时读取 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)。

涉及 DDD 时，bounded context 仍由项目领域模型决定；不要把代码 seam 与领域边界混为一谈。
