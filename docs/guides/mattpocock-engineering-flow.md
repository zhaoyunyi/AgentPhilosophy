# Matt Pocock Skills 产品工程主线

AgentPhilosophy 默认 preset 会同步 `skill-mattpocock-engineering`。该模块改编自 Matt Pocock 的 `mattpocock/skills`，用于把模糊想法推进到可交付实现，同时保留项目领域语言、spec、ticket 和验证证据。

上游来源：https://github.com/mattpocock/skills

## 推荐主线

```text
/grill-with-docs
-> /to-spec
-> /to-tickets
-> 新开会话逐个 ticket 用 /implement
```

含义：

- `/grill-me`：只做一问一答的无文档拷问；需要沉淀领域语言和决策时改用 `/grill-with-docs`。
- `/grill-with-docs`：先拷问计划、决策或想法，同时沉淀 `CONTEXT.md`、ADR 和领域语言。
- `/to-spec`：把已经讨论清楚的内容整理成 spec，不重新访谈。
- `/to-tickets`：把 spec 拆成独立、可验证的 tracer-bullet vertical slice ticket。
- `/implement`：按单个 spec/ticket 实现，内部倾向走 `/tdd`，最后跑 `/code-review`。
- `/to-prd` 与 `/to-issues`：保留给已有项目兼容调用。

## 上下文切分

`/grill-with-docs`、`/to-spec` 和 `/to-tickets` 尽量放在同一个连续会话里完成，避免中途压缩后丢失需求细节。如果上下文接近上限，先写 handoff 文档，再在新会话恢复。

`/implement` 应该逐个 ticket 新开会话：新会话只带 spec、单个 ticket、项目规则和必要代码上下文。这样每个实现会话能保持窄范围，减少串改。

## 文档沉淀边界

- `CONTEXT.md` 只写领域词汇和统一语言，不写 PRD、任务清单或实现细节。
- ADR 只记录难反转、没有上下文会显得奇怪、且有真实权衡的决定。
- Spec 描述用户问题、解决方案、user stories、已确认技术决策、测试决策和非目标。
- Ticket 必须是 vertical slice：完成后能单独演示或验证，不按 schema/API/UI 水平层拆散。
- 未配置 tracker 时，每个 ticket 单独写入 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，并标记 `Status: ready-for-agent`。

## 实现和验证

`/implement` 的默认顺序：

1. 读取 spec 和单个 ticket。
2. 明确测试 seam。
3. 用 `/tdd` 做一个失败测试、一个最小实现、一次局部验证。
4. 重复到 acceptance criteria 覆盖完成。
5. 运行完整验证命令。
6. 用 `/code-review` 分别检查 Standards 和 Spec。
7. 按项目版本控制规则提交；jj 仓库使用 `jj describe`、`jj new` 和 `jj git push`。

## 旧项目升级

新项目使用默认 preset 时会自动包含 `skill-mattpocock-engineering`。旧项目的 `.agentphilosophy.yaml` 模块列表是显式冻结的，升级 CLI 不会自动追加模块。需要引入这组 skill 时，追加模块后同步：

```yaml
modules:
  - existing-module
  - skill-mattpocock-engineering
```

然后执行：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

同步后应能看到：

```bash
find /path/to/project/.codex/skills -maxdepth 2 -name SKILL.md | sort
```

其中包括 `grill-me`、`grill-with-docs`、`to-spec`、`to-tickets`、兼容入口 `to-prd`、`to-issues`，以及 `implement`、`tdd` 和 `code-review`。
