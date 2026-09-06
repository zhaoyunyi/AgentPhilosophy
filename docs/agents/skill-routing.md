# Skill 路由验收场景

这些场景用于修改 skill 描述或调用策略后的人工/模型路由验收。自动测试验证生成文件、metadata 和显式配置，Codex `skills/list` 验证实际发现；二者都不替代模型在自然语言输入下的选择效果。本轮没有为这些场景发起付费模型评测。

| 输入场景 | 预期行为 | 关键反例 |
| --- | --- | --- |
| “检查当前 AGENTS.md 是否合理” | 当前快照审查，必要时读 writing-for-agents | 不因没有 diff 或比较点而停下；不自动同步或提交 |
| “同步规范到这个已有项目” | agentphilosophy-sync，读取接入状态与迁移合同 | 不覆盖非托管内容，不先恢复全局 Superpowers |
| “修复已明确的复制路径越界” | coding-standards/TDD，从公共 CLI 验证失败和成功路径 | 不为缺少 CONTEXT.md 创建空文档，不重复询问已确认范围 |
| “我们的 CI 构建变慢了” | optimize-build-pipeline，先取实际耗时与资源证据 | 不先预测提升幅度，不削弱发布门禁 |
| “Python 同步工具的文档有错字” | 精确文档修正 | 不安装 Portless、Node 或安全工具，不触发 reverse-skill |
| “分析已授权测试样本的 JS 签名” | reverse-skill，按当前授权与 routing.json 选择路径 | 不把 precedent、目标名或 Force 退出码当成授权 |
| “使用 Superpowers 做这个设计” | 核对实际安装后按明确选择使用 | 普通设计请求不全局强制启用；已有授权不重复索取 |
| 项目未配置 matt_implicit_skills 的普通开发请求 | to-spec/to-tickets/implement 保持显式入口 | 不因已经安装就扩大隐式调用集 |
| 项目明确配置 implement 为隐式可用 | 相关实现任务可发现 implement，支持文件完整 | to-prd/to-issues/writing-great-skills 等兼容入口仍仅显式使用 |
| “阅读生成结果里的 provider 字段含义” | 根据开发者受众提供公开合同解释 | 不将普通门户禁词扩展成开发者文档一律不许解释技术词 |

新增场景应写清输入、预期选择、禁止副作用和是否实际执行；记录观察结果时区分模型推断、metadata 校验与宿主回读。技能描述将关键用途和触发词放在前面，减少重复项目名和无行为价值的前缀。
