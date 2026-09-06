---
name: philosophy-extraction
description: 从哲学/概念性文章中提取可操作的 Agent 决策框架，生成冲突解决协议模板并集成到 aphilosophy 模块。适用于处理赛博经藏系列或类似的将哲学映射为 AI 工程原则的文章。
---

# Philosophy Extraction Skill

将哲学/概念性文章"脱水"为可计算的 Agent 决策规则，产出标准化的冲突解决协议模板。

## 核心理念

哲学文章对 Agent 的价值不在于"理解哲学"，而在于提取出**可在运行时执行的决策规则**。这个过程叫"脱水"——去掉哲学包装，保留操作性内核。

关键判断标准：**如果一条原则不能被转化为"当 X 条件成立时，执行 Y 行为"的形式，它就不应该进入模板。**

## 工作流程

### 阶段 0：判断当前工作区类型

先判断当前目录是 AgentPhilosophy 中央源，还是已接入 AgentPhilosophy 的目标项目。

| 工作区类型 | 判断信号 | 写入策略 |
|------|------|------|
| AgentPhilosophy 中央源 | 同时存在 `catalog.yaml`、`modules/`、`src/agentphilosophy/default_source/` | 可以修改 `modules/aphilosophy/`、packaged source、catalog 和 CLI 文档 |
| 目标项目 | 存在 `.agentphilosophy.yaml`、`.agents/agentphilosophy-state.yaml` 或生成的 `aphilosophy/` | 不要直接改托管的 `aphilosophy/`；先输出候选协议到 `.agents/custom/aphilosophy-extraction/`，再建议回中央源集成 |

如果只是目标项目需要一次性吸收某篇文章的原则，不要把生成内容直接写进受 AgentPhilosophy 管理的 `aphilosophy/*.md`。这些文件下一次 `agentphilosophy-sync push --apply` 可能被覆盖。需要长期分发时，应回到中央源按“中央源集成”流程修改模块模板。

### 阶段 1：获取文章内容

1. 只处理用户有权访问或已经提供的文章内容；不要绕过登录、付费、权限、反爬或访问控制。
2. 使用 CDP 浏览器模式获取用户已授权访问的文章（微信公众号等动态页面）。
3. 分段提取必要内容（每段 8000 字符以内）；长文只保留完成分析所需的摘要、结构和短摘录。
4. 提取完成后关闭 tab，并避免在最终回复中大段复现原文。

### 阶段 2：批判性分析

对文章进行严格评估，产出结构化分析：

**评估维度：**

| 维度 | 问题 |
|------|------|
| 映射质量 | 哲学概念到工程概念的映射是否精确？还是只是修辞上的类比？ |
| 虚假精确 | 是否用哲学术语包装了本来就显而易见的工程常识？ |
| 可操作性 | 提出的原则能否被转化为具体的判断标准和行动指令？ |
| 过度延伸 | 哪些映射是牵强的、为了完整性而凑数的？ |
| 独特贡献 | 这篇文章提供了什么其他框架（纯工程思维）无法提供的视角？ |

**输出格式：**
```
## [文章标题] 分析

### 优点
1. [具体优点 + 为什么有价值]
...

### 问题
1. [具体问题 + 为什么是问题]
...

### 可提取的操作性原则
1. [原则名称]：[一句话描述可计算的决策规则]
...
```

### 阶段 3：模板生成

将提取的原则转化为标准格式的冲突解决协议模板。

**文件命名规则：** `{domain}-conflict-resolution.md.j2`

- 架构设计相关 → `architecture-conflict-resolution`
- 多主体治理相关 → `governance-conflict-resolution`
- 自我认知/推理相关 → `cognitive-conflict-resolution`
- 权限/对齐/服从相关 → `authority-conflict-resolution`
- 新领域 → 根据内容确定合适的 domain 名称

**每个冲突类型的标准结构：**

```markdown
## 冲突类型 N：[简短标题]——[张力的两端]

场景：[一句话描述触发此冲突的具体情境]

### 决策原则：[一句话核心规则]

[1-2 句解释为什么这个原则有效]

### 判断标准

- [具体的、可检查的条件 1]
- [具体的、可检查的条件 2]
- [具体的、可检查的条件 3]

### 行动

- [条件] → [具体行为]
- [条件] → [具体行为]
- [条件] → [具体行为]

### 禁止行为

- [具体的反模式描述]
- [具体的反模式描述]
```

**质量检查清单：**

- [ ] 每个"判断标准"都是 Agent 可以自检的问题（不是抽象描述）
- [ ] 每个"行动"都有明确的触发条件和具体行为（不是"视情况而定"）
- [ ] 每个"禁止行为"都是可识别的具体模式（不是"不要做坏事"）
- [ ] 没有哲学术语残留（如果必须用，已经给出了工程定义）
- [ ] 冲突类型之间没有重叠（每个场景只匹配一个类型）

### 阶段 4A：中央源集成

1. **放置模板文件**
   ```
   modules/aphilosophy/templates/{domain}-conflict-resolution.md.j2
   ```

2. **更新 module.yaml**
   - 递增 version（minor 版本）
   - 在 `provides` 中添加 `philosophy:{domain}-conflicts`
   - 在 `outputs` 中添加新条目

3. **更新 catalog.yaml**
   - 更新 description
   - 在 outputs 列表中添加新文件路径

4. **同步 packaged source**
   ```bash
   cp modules/aphilosophy/templates/{new-file} src/agentphilosophy/default_source/modules/aphilosophy/templates/
   cp modules/aphilosophy/module.yaml src/agentphilosophy/default_source/modules/aphilosophy/module.yaml
   cp catalog.yaml src/agentphilosophy/default_source/catalog.yaml
   ```

5. **更新 LLM 使用入口**
   - 在 `docs/cli-usage-for-llm.md` 的 Agent 哲学决策框架章节添加新协议的触发式读取规则
   - 同步 `src/agentphilosophy/default_source/docs/cli-usage-for-llm.md`

6. **验证**
   ```bash
   uv run pytest -q  # 全部通过
   # 验证模板渲染
   uv run python -c "
   from jinja2 import Environment, FileSystemLoader
   env = Environment(loader=FileSystemLoader('modules/aphilosophy/templates'))
   tmpl = env.get_template('{domain}-conflict-resolution.md.j2')
   print(tmpl.render())
   "
   ```

### 阶段 4B：目标项目候选输出

当当前目录是普通目标项目时，只生成候选材料，不直接覆盖托管文档：

1. **放置候选协议**
   ```
   .agents/custom/aphilosophy-extraction/{domain}-conflict-resolution.md
   ```

2. **记录来源与判断**
   - 同目录放置 `{domain}-analysis.md`，包含文章标题、提取日期、可操作原则和被丢弃内容。
   - 明确说明该候选尚未进入中央 `aphilosophy` 模块，不会被安装版 CLI 分发给其他项目。

3. **需要长期分发时**
   - 回到 AgentPhilosophy 中央源执行“阶段 4A：中央源集成”。
   - 完成后用安装版或源码版 CLI 对目标项目执行 `validate`、`push --dry-run`、`push --apply`。

## 脱水原则——什么该留，什么该扔

### 留下的（可操作）

| 特征 | 示例 |
|------|------|
| 有明确触发条件 | "当同一方法连续失败 2 次时" |
| 有具体行为指令 | "停止优化方法，重新评估适用性" |
| 有可检查的判断标准 | "我是否在想'这个规则太保守了'？" |
| 提供了新的决策维度 | 五级行为分类替代二元允许/禁止 |
| 解决了真实的 Agent 困境 | 递归自省的终止条件 |

### 扔掉的（不可操作）

| 特征 | 示例 |
|------|------|
| 纯修辞类比 | "System Prompt 就是神说要有光" |
| 无法判断的标准 | "达到涅槃般的零附着状态" |
| 重复已有工程常识 | "代码要模块化"（用哲学包装） |
| 过度抽象 | "万物皆空"→ 无法转化为具体行为 |
| 文化评论 | "AGI 是弥赛亚"（有趣但不产生决策规则） |

## 已有模板索引

维护中央源时，以 `modules/aphilosophy/module.yaml` 的 `outputs` 为权威清单；说明与来源映射见 `docs/guides/aphilosophy-methodology.md`。先核对现有元决策、架构、治理、认知、权限、运行态和安全对抗条目，再判断是否需要新增领域；本入口不另存一份易漂移的表格。

## 注意事项

- 一篇文章通常只产出一个模板文件，对应一个冲突领域
- 如果文章内容跨多个领域，优先提取该文章独特贡献最大的领域
- 元决策原则（meta-decision-principles）是所有冲突协议的上层锚点，新模板不应与之矛盾
- 冲突类型数量控制在 5-8 个，太少说明提取不充分，太多说明粒度太细
- 模板中不引用哲学来源——价值在于指导行为，不在于展示学识
