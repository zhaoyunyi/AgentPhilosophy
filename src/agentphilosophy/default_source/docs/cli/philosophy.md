## 十三、Agent 哲学决策框架

`aphilosophy` 模块会生成一组触发式参考文档。LLM 不需要在每次任务开始时全量读取它们；只有当任务进入对应冲突或权衡场景时，才按需读取。

- 遇到跨协议冲突、任务妥协、方向选择或连续尝试失败时，读取 `aphilosophy/meta-decision-principles.md`。
- 遇到架构设计、技术选型、抽象层增减、配置化取舍或系统退化判断时，读取 `aphilosophy/architecture-conflict-resolution.md`。
- 遇到多 Agent 协作、角色边界、用户沟通、命名歧义、治理层级或行为校准问题时，读取 `aphilosophy/governance-conflict-resolution.md`。
- 遇到推理前提、方法论失效、递归自省、不确定性分级、错误严重度或能力边界判断时，读取 `aphilosophy/cognitive-conflict-resolution.md`。
- 遇到系统规则、开发者指令、权限边界、服从与自主判断、已授权的应急响应或失对齐风险时，读取 `aphilosophy/authority-conflict-resolution.md`。

这些文档是通用决策锚点，不覆盖项目自己的 `AGENTS.md`、`spec/` 或 `.agents/custom` 规则。若哲学框架与项目特定规范冲突，以项目特定规范为准；若项目规范前提已经失效，应先向用户说明观察到的事实，再提出可验证的调整建议。

当前中央源还提供可选模块 `skill-philosophy-extraction`。该模块不会默认出现在 preset 中；只有当目标项目需要维护或扩展 `aphilosophy` 决策框架、从哲学/概念性文章中提取可操作规则、生成新的冲突解决协议模板时，才把它加入目标项目 `.agentphilosophy.yaml`。该模块依赖 `aphilosophy`，不能单独启用；加入后，安装版 CLI 会同步生成 `skills/philosophy-extraction/SKILL.md` 和 `.agents/skills/philosophy-extraction/SKILL.md`，让 Codex 原生 skill discovery 能在目标项目内触发。

```yaml
modules:
  - aphilosophy
  - skill-philosophy-extraction
```

启用后仍必须执行标准同步流程：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```
