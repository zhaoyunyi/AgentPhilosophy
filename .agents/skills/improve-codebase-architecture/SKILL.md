---
name: improve-codebase-architecture
description: 为 AgentPhilosophy 发现架构摩擦、浅模块和难测试接口，产出架构评审 HTML 报告与可执行的深模块重构候选。适用于用户要求改进架构、寻找重构机会、合并紧耦合模块、提高可测试性，或让代码库更容易被 agent 导航。
---

# Improve Codebase Architecture

> 改编自 Matt Pocock 的 `improve-codebase-architecture` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/improve-codebase-architecture

目标：发现代码库里的架构摩擦，提出能把 shallow modules 变成 deep modules 的重构候选。先做评审和候选报告，不在用户选择前直接改代码。

使用同目录 `HTML-REPORT.md` 作为报告内容合同；为选中候选设计 Interface 与 seam 时调用 `/codebase-design`。

## 核心词汇

评审、报告和建议中统一使用这些术语，避免把架构讨论写散：

| 术语 | 含义 | 避免替换成 |
| --- | --- | --- |
| Module | 任何同时有 interface 和 implementation 的单元，可以是函数、类、包或跨层切片。 | component、service、unit |
| Interface | 调用方必须知道才能正确使用 Module 的全部事实，包括类型、约束、错误模式、顺序、配置和性能特征。 | API、signature |
| Implementation | Module 内部的代码和协作细节。 | - |
| Depth | Interface 背后隐藏的行为杠杆。Deep 表示小 interface 后面有大量行为；Shallow 表示 interface 几乎和 implementation 一样复杂。 | 代码行数比例 |
| Seam | 可以替换行为而不在原地编辑的位置，也就是 interface 所在的位置。 | boundary |
| Adapter | 满足某个 seam 上 interface 的具体实现。 | - |
| Leverage | 调用方从 deep module 得到的收益：更少 interface 学习成本换更多行为。 | - |
| Locality | 维护者从 deep module 得到的收益：变更、 bug、知识和验证集中在一个地方。 | - |

三个判断锚点：

- **Deletion test**：想象删除这个 Module。复杂度是消失了，还是分散回多个调用方？如果只是分散回去，它原本在隐藏复杂度。
- **The interface is the test surface**：调用方和测试应穿过同一个 interface。
- **One adapter = hypothetical seam. Two adapters = real seam**：只有一个 adapter 时不要为了形式抽象引入 seam。

## 先读取的项目事实

进入代码探索前先按需读取，读取不到就跳过，不要伪造事实：

1. 当前目录的 `AGENTS.md`、`CLAUDE.md`、README 和用户给出的任务边界。
2. AgentPhilosophy ArchitectureSpec 和领域规范：`spec/ArchitectureSpec.md`、`spec/DDDSpec.md`、`spec/BDDSpec.md`、`spec/TestStrategy.md`。
3. 项目自己的领域语言：根目录 `CONTEXT.md`、`CONTEXT-MAP.md` 或相关子目录里的 `CONTEXT.md`。
4. 架构决策：`docs/adr/`、`docs/decisions/`、OpenSpec change、架构 runbook。
5. 如果存在 `aphilosophy/architecture-conflict-resolution.md`，用它校准抽象增减、配置化取舍和系统退化判断。

不要用本 skill 重新辩论已有 ADR。只有当真实摩擦足够强、值得重开决策时，才在报告中标明“与 ADR-NNNN 冲突，但值得重新评估”。

## 流程

### 1. Explore

先按 YAGNI 收窄扫描范围。用户点名模块、子系统或痛点时以该方向为准；否则读取近期约 20 条 change/commit 描述，优先检查持续发生变更的热区。若历史变化分散、没有可信热区，再扩大范围。深模块只有在未来仍会被修改时才产生 leverage，不把休眠代码的整洁度当成优先候选。

沿真实代码路径探索，不套固定 checklist。重点记录你实际遇到的理解和验证摩擦：

- 理解一个业务概念是否需要在很多小 Module 之间来回跳转。
- 某个 Module 是否 shallow：interface 学习成本接近 implementation 复杂度。
- 是否有为了单元测试而抽出的纯函数，但真正的 bug 藏在调用组合里，缺少 locality。
- 紧耦合 Module 是否把知识漏过 seam，让调用方理解太多内部细节。
- 哪些行为只能通过实现细节测试，不能通过稳定 interface 测试。
- 哪些配置、错误处理、重试、权限或状态机逻辑分散在多个调用方。

可以并行使用子 agent 做只读探索，但每个子 agent 必须有清晰文件范围，且只返回候选和证据，不改文件。没有子 agent 能力时，自己分区探索即可。

### 2. 写 HTML 候选报告

把报告写到系统临时目录，避免把未确认方案落进仓库：

- macOS/Linux：优先 `$TMPDIR`，缺失时用 `/tmp`。
- Windows：优先 `%TEMP%`。
- 文件名：`architecture-review-<timestamp>.html`。

报告必须是单文件 HTML。可以使用 Tailwind CDN 做布局，Mermaid CDN 做依赖图、调用图或时序图；关系不是图结构时，用手写 CSS/SVG/HTML 画 before/after。每个候选都要有可视化，不只写文字。

每个候选卡片包含：

- **Files**：涉及的文件和 Module。
- **Problem**：当前 architecture friction 是什么。
- **Solution**：要把哪些 shallow modules deepen 成什么 Module。
- **Benefits**：用 leverage、locality 和 test surface 解释收益。
- **Before / After diagram**：展示 shallow 状态和 deepened 状态。
- **Recommendation strength**：`Strong`、`Worth exploring` 或 `Speculative`。
- **ADR conflict**：如有真实冲突，标明冲突的 ADR 和为什么值得重开。

报告末尾必须有 **Top recommendation**：先做哪一个候选，以及为什么。

写完后打开报告：

- macOS：`open <path>`
- Linux：`xdg-open <path>`
- Windows：`start <path>`

然后告诉用户绝对路径，并问：`你想先深入哪一个候选？`

### 3. 用户选择后的 grilling loop

用户选择候选后，再进入设计追问和接口探索：

1. 明确候选背后的约束、依赖类别、seam 放置点和测试面。
2. 如果当前工具链支持并行子 agent，让 3 个以上子 agent 生成差异足够大的 interface 设计：
   - 最小 interface：1-3 个入口，最大化 leverage。
   - 灵活 interface：覆盖更多用例和扩展点。
   - 调用方优化 interface：让最常见调用最简单。
   - ports & adapters：当依赖跨进程或外部服务时使用。
3. 顺序展示方案，用 depth、locality、seam placement 和测试稳定性比较。
4. 给出明确推荐；如果混合方案更强，说明混合边界。

如果设计过程中出现新的领域名词：

- 先确认它是项目领域概念，不是一般编程术语。
- 若是领域概念，更新对应 `CONTEXT.md`；没有时按需创建根目录 `CONTEXT.md`。
- 若用户拒绝某候选且理由长期有效、未来 reviewer 也需要知道，询问是否记录 ADR。只在决策难反转、没有上下文会显得奇怪、且存在真实权衡时写 ADR。

### 4. 进入实现时的边界

只有用户明确选择候选并要求实现后，才改代码。实现时遵守项目自己的 coding/test skill：

- 先补失败测试或 BDD 场景，覆盖用户可见行为和关键失败路径。
- 新 interface 的测试应穿过 Module interface，不测试 implementation 私有细节。
- 当 deep module 的 interface 测试已经覆盖旧行为，删除只验证 shallow wrapper 的旧测试。
- 分阶段提交：先收敛 interface 和调用方，再清理旧 Module，不混入无关重构。
- 完成前运行项目配置的验证命令：`uv run pytest -q`。

## 不做的事

- 不把架构评审报告写入仓库，除非用户明确要求沉淀为文档。
- 不为了“更干净”提出没有真实 friction 的抽象。
- 不把一个 adapter 包装成 seam。
- 不在候选报告阶段直接改代码。
- 不绕过项目已有 ADR、OpenSpec、BDD 或用户明确给出的架构边界。
