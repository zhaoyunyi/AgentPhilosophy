---
name: to-issues
description: 把 AgentPhilosophy 的 PRD、计划或 spec 拆成可独立认领的 issue；适用于用户输入 /to-issues、要求按 vertical slice 拆分 PRD，或需要为多个 agent/会话准备实现任务。
---

# To Issues

兼容别名：Matt Pocock 当前上游已把 `to-issues` 更新为 `to-tickets`。新流程优先使用 `/to-tickets`，本 skill 保留给已有项目、脚本或团队习惯继续调用。

改编自 Matt Pocock 的 `to-tickets` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/to-tickets

目标：把 PRD 拆成独立、可验证、可交给新会话的 vertical slice issue。

## 流程

1. 读取 PRD、当前对话、相关代码和项目领域词。若用户给了 issue、URL 或路径，先读取完整内容。
2. 必要时快速探索代码，寻找能让实现更容易的 prefactoring 机会。
3. 按 vertical slice 拆分：每个 issue 都贯穿数据、API、UI、测试或对应集成层，交付一个可演示或可验证的窄行为。
4. 为每个 issue 标出 blocking edges：哪些 issue 必须先完成，没有则写 `None - can start immediately`。
5. 先展示拆分草案，等待用户确认粒度、依赖和覆盖范围。
6. 用户确认后再发布 issue：
   - 已配置 issue tracker 时，按依赖顺序发布，阻塞项先发。
   - 使用本地模式或没有 tracker 时，把每个 issue 分别写入 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`；每个 issue 一个文件，不生成合并的 `issues.md`。
7. 发布后明确当前工作前沿（work frontier）：列出所有 `Blocked by: None - can start immediately` 的 issue，便于 agent 立即认领。

## 草案格式

每个候选 issue 展示：

- **Title**：短标题。
- **Blocked by**：依赖哪些 issue，没有则写 `None`。
- **User stories covered**：覆盖的 PRD user stories。
- **Verification**：完成后如何证明。

## Issue 模板

```markdown
**Status:** ready-for-agent

## Parent

父 PRD 或父 issue 链接。

## What to build

描述端到端行为，不按层分配任务。

## Acceptance criteria

- [ ] 用户可见成功路径。
- [ ] 关键失败路径。
- [ ] 验证命令或证据。

## Blocked by

None - can start immediately
```

## 注意

- 不要把 “先写 schema”“再写 API”“最后写 UI” 拆成水平层 issue，除非其中某个 slice 本身就是可验收行为。
- 不关闭或修改父 issue。
- 每个 issue 都应足够独立，后续新会话可以只拿 PRD + 单个 issue 运行 `/implement`。
- 本地 issue 必须每个 issue 一个文件；文件编号按依赖顺序递增，不能把所有 issue 合并成一个文件。
