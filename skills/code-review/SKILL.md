---
name: code-review
description: 对 AgentPhilosophy 的分支、PR 或工作区改动做双轴 review；适用于用户输入 /code-review、要求 review since 某个固定点，或 /implement 完成后需要检查标准和 spec 覆盖。
---

# Code Review

改编自 Matt Pocock 的 `code-review` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/code-review

目标：把 review 分成两个轴，避免“代码看起来干净”掩盖“实现错了”，也避免“实现对了”掩盖“项目标准破了”。

## 两个轴

- **Standards**：是否符合本仓 `AGENTS.md`、spec、coding standards、测试和文案红线。
- **Spec**：是否忠实实现来源 PRD、issue、OpenSpec change 或用户给定需求。

## 流程

1. 固定比较点。用户没给时先问；可用 `main`、tag、change id、commit 或 PR base。
2. 确认 diff 非空。jj 仓库优先用 `jj diff -r <base>..@` 或项目推荐 revset；普通 git 仓库用 `git diff <fixed-point>...HEAD`。
3. 找 spec 来源：commit/change 描述、issue、PRD、OpenSpec、用户传入路径或 docs/spec 文件。没有 spec 时明确标记 Spec 轴无法完整判断。
4. 找 standards 来源：`AGENTS.md`、`CLAUDE.md`、`spec/`、`CONTRIBUTING.md`、测试策略和项目内 skill。
5. 如果工具支持并行子 agent，Standards 与 Spec 分开审；否则自己分两段审，避免混合排序。
6. Findings 优先，按严重度列文件和行号；没有问题也说明剩余风险和未覆盖验证。

## 报告格式

```markdown
## Standards

- [P1] <file:line> <问题>

## Spec

- [P1] <file:line> <问题>

## Open Questions

- <需要用户确认的边界>

## Verification

- <已运行或建议运行的命令>
```

## 判断基线

即使项目没有明确 coding standards，也检查常见设计异味：mysterious name、duplicated code、feature envy、data clumps、primitive obsession、repeated switches、shotgun surgery、divergent change、speculative generality、message chains、middle man、refused bequest。把这些作为判断型发现，不把工具已覆盖的问题重复上报。
