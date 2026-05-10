# AgentPhilosophy Agent 协作规范

> 中央 Agent 协作规范同步工具

## 通用约定

- 默认继承当前会话模型和 reasoning，不为子任务随意指定更弱模型。
- 只有任务能并行、写入范围清晰且不会阻塞主路径时才使用多 agent。
- 子 agent 修改代码时必须说明负责文件范围，并避免覆盖其他人改动。
- 使用中文交流和回复。
- 文档使用中文 Markdown 格式。
- 如果仓库存在 `.jj/`，默认使用 jj 工作流处理提交、同步和 bookmark。
- 按功能领域拆分中文 change 描述，避免把无关文件混进同一个提交。
- 推送 `main` 或同步主线时，必须同时确认远端 bookmark 和默认工作区状态。
- 进入子目录前先读取该目录内的 `AGENTS.md`、`CLAUDE.md` 或 README。
- 跨仓搜索默认只读；除非任务明确要求，不修改兄弟仓或外部项目文件。


## 工程规范

- 涉及领域模型时先明确实体、值对象、聚合和边界上下文。
- 不为技术便利跨越领域边界共享内部状态。
- 完成前必须运行最新验证命令，不能用旧日志或推测替代。
- 用户流程变更必须补充 BDD 场景，覆盖成功路径和关键失败路径。
- BDD 断言应面向行为结果，不绑定内部实现细节。


## 项目扩展

项目特有内容应放在 `.agents/custom`，避免中央同步覆盖手写规则。

## Superpowers System

<EXTREMELY_IMPORTANT>
Superpowers 已通过 **Codex 原生 skill discovery** 安装，无需再使用旧版 `superpowers-codex bootstrap`。

固定安装位置：

- Superpowers 仓库：`~/.codex/superpowers`
- Skills 入口（symlink）：`~/.agents/skills/superpowers` -> `~/.codex/superpowers/skills`

如果某次会话中技能未出现：先确认上述 symlink 存在，再重启 Codex CLI。
</EXTREMELY_IMPORTANT>
