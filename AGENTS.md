# AgentPhilosophy Agent 协作规范

> 中央 Agent 协作规范同步工具

## 通用约定

- 根据任务复杂度、风险、不确定性、时效和成本，选择合适的模型与推理强度。
- 高风险、跨模块、难验证或证据不足的任务，优先使用能力更强的模型和更充分的推理。
- 机械、低风险、边界清晰且容易验证的任务，可以使用更轻量的模型与推理强度。
- 只有任务可独立推进、职责清晰且写入范围不冲突时才使用多 agent。
- 为子 agent 明确目标、负责范围、输入、预期产物和验收标准；修改代码时避免覆盖其他 agent 或用户的改动。
- 使用中文交流和回复。
- 文档使用中文 Markdown 格式。
- 默认使用 jj colocated git 管理当前仓库；如果仓库还没有 `.jj/`，先执行 `jj git init --colocate`。
- 如果 `command -v jj` 找不到 jj CLI，先安装 jj：macOS 优先使用 `brew install jj`，没有 Homebrew 时按本机包管理器或官方安装方式安装。
- 当前仓库存在 `.jj/` 后，本地版本控制操作使用 `jj status`、`jj log`、`jj diff`、`jj describe`、`jj new`、`jj bookmark` 和 `jj git push`，不要再用 `git add`、`git commit`、`git stash` 或 `git checkout` 管理本地变更。
- 按功能领域拆分中文 change 描述，避免把无关文件混进同一个提交。
- 推送 `main` 或同步主线时，必须同时确认远端 bookmark 和默认工作区状态。
- 进入子目录前先读取该目录内的 `AGENTS.md`、`CLAUDE.md` 或 README。
- 跨仓搜索默认只读；除非任务明确要求，不修改兄弟仓或外部项目文件。


## 工程规范

- 新增、迁移或沉淀长期文档时，必须同步更新主入口、相关目录索引（例如 `docs/README.md`）或 `.agents/custom` 中的 layered custom 源，避免正文无入口。
- 涉及领域模型时先明确实体、值对象、聚合和边界上下文。
- 不为技术便利跨越领域边界共享内部状态。
- 完成前必须运行最新验证命令，不能用旧日志或推测替代。
- 用户流程变更必须补充 BDD 场景，覆盖成功路径和关键失败路径。
- BDD 断言应面向行为结果，不绑定内部实现细节。

- 用户可见文案不得解释内部实现、上游供应商或产品内部边界；只表达用户能理解的对象、状态、影响和下一步。
- 不用文案区分产品 key 与上游或供应商 API key；例如 “组织访问密钥用于服务端集成；它不是上游 API key。” 这类说明只能留在内部 spec、测试或运维文档，不进入页面、toast、空状态、按钮、客户可读错误或公开文档。
- 避免在 UI 中渲染 provider binding、allowlist、resource policy、runtime provider、adapter、raw refs、capability key、secret hash、trace、raw payload 等内部词和值；需要展示时先映射成产品化状态。
- 涉及中英文文案时两种语言都按同一红线排查；不能只删中文或英文一边。
- 用户流程变更或文案红线修复要补相应 unit、e2e 或 BDD 守卫，断言面向渲染结果而不是实现细节。

## 项目扩展

项目特有内容应放在 `.agents/custom`，避免中央同步覆盖手写规则。
