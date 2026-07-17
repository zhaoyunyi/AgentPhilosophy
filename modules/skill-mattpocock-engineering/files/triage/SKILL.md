---
name: triage
description: 让外部 issue 或明确纳入的 PR/MR 经过分类、核实、澄清和状态迁移，最终形成可由 agent 接手的 brief。
disable-model-invocation: true
---

# Triage

改编自 Matt Pocock 的 `triage` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/triage

先读取 `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和 `docs/agents/domain.md`。缺少配置时先运行 `/setup-matt-pocock-skills`。所有由 AI 写入 tracker 的 triage 评论以以下声明开头：

```markdown
> 此内容由 AI 在需求分流过程中生成。
```

## 状态模型

- 分类：`bug` 或 `enhancement`。
- 状态：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。
- 每个完成分流的对象恰有一个分类和一个状态；冲突标签先交给维护者确认。

## 查看待处理项

按最早优先列出：未分类、`needs-triage`、报告者有新回复的 `needs-info`。仅在 tracker 配置明确允许时包含外部 PR/MR；维护者自己的在途变更不当成 triage 输入。

## 处理单项

1. 读取正文、评论、标签、作者、时间；PR/MR 同时读 diff。读取相关 glossary、ADR 和代码。
2. 以领域概念搜索是否已实现；再搜索 `docs/agents/out-of-scope/` 是否已有拒绝记录。
3. 向维护者推荐分类与状态，说明代码证据，等待方向。
4. 对 bug 复现症状；对 PR/MR 运行相关验证。报告确认、未复现或信息不足。
5. 信息不足时联合 `/grilling` 与 `/domain-modeling`，每次只解决一个问题。
6. 应用结果：
   - `ready-for-agent`：按 [AGENT-BRIEF.md](AGENT-BRIEF.md) 发布可持久 brief。
   - `ready-for-human`：同样写 brief，并注明不能委派的判断或权限。
   - `needs-info`：列出已确认事实和对报告者的具体问题。
   - `wontfix`：已实现则指向现有能力；拒绝 enhancement 时按 [OUT-OF-SCOPE.md](OUT-OF-SCOPE.md) 记录；bug 拒绝不进入需求知识库。

维护者明确要求快速切换状态时，先确认即将发生的标签、评论和关闭动作，再执行；没有 brief 时询问是否补写。
