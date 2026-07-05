# Matt Pocock Skills 产品工程主线

AgentPhilosophy 默认 preset 会同步 `skill-mattpocock-engineering`。该模块改编自 Matt Pocock 的 `mattpocock/skills`，用于把模糊想法推进到可交付实现，同时保留项目领域语言、PRD、issue 和验证证据。

上游来源：https://github.com/mattpocock/skills

## 推荐主线

```text
/grill-with-docs
-> /to-prd
-> /to-issues
-> 新开会话逐个 issue 用 /implement
```

含义：

- `/grill-with-docs`：先拷问需求和设计，同时沉淀 `CONTEXT.md`、ADR 和领域语言。
- `/to-prd`：把已经讨论清楚的内容整理成 PRD，不重新访谈。
- `/to-issues`：把 PRD 拆成独立、可验证、适合新会话认领的 vertical slice issue。
- `/implement`：按单个 PRD/issue 实现，内部倾向走 `/tdd`，最后跑 `/code-review`。

## 上下文切分

`/grill-with-docs`、`/to-prd` 和 `/to-issues` 尽量放在同一个连续会话里完成，避免中途压缩后丢失需求细节。如果上下文接近上限，先写 handoff 文档，再在新会话恢复。

`/implement` 应该逐个 issue 新开会话：新会话只带 PRD、单个 issue、项目规则和必要代码上下文。这样每个实现会话能保持窄范围，减少串改。

## 文档沉淀边界

- `CONTEXT.md` 只写领域词汇和统一语言，不写 PRD、任务清单或实现细节。
- ADR 只记录难反转、没有上下文会显得奇怪、且有真实权衡的决定。
- PRD 描述用户问题、解决方案、user stories、已确认技术决策、测试决策和非目标。
- Issue 必须是 vertical slice：完成后能单独演示或验证，不按 schema/API/UI 水平层拆散。

## 实现和验证

`/implement` 的默认顺序：

1. 读取 PRD 和单个 issue。
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

其中包括 `grill-with-docs`、`to-prd`、`to-issues`、`implement`、`tdd` 和 `code-review`。
