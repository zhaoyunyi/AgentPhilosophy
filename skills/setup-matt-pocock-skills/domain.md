# 领域文档消费规则

探索代码前按需读取：

- 根 `GLOSSARY.md`，或 `GLOSSARY-MAP.md` 指向的相关上下文。
- `docs/adr/` 与相关上下文内部 ADR。
- AgentPhilosophy 项目的 `spec/DDDSpec.md`、`spec/ArchitectureSpec.md` 及相关 feature spec。

文件不存在时继续工作，不为了填目录提前制造空文档。`/domain-modeling` 在真正澄清术语或决策时再创建。

## 布局

单上下文默认：

```text
GLOSSARY.md
docs/adr/
spec/
```

多上下文仅在边界真实存在时使用：

```text
GLOSSARY-MAP.md
docs/adr/                  # 系统级决策
src/<context>/GLOSSARY.md
src/<context>/docs/adr/   # 上下文决策
```

输出中的实体、值对象、聚合、测试名和 issue 标题应使用 glossary 已定义词汇。若结论与 ADR 冲突，显式指出并说明是否建议重开决策，不静默覆盖。
