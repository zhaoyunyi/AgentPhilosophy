# AgentPhilosophy Agent 协作规范

> 中央 Agent 协作规范同步工具

## 通用约定

- 根据任务复杂度、风险、不确定性、时效和成本，选择合适的模型与推理强度。
- 高风险、跨模块、难验证或证据不足的任务，优先使用能力更强的模型和更充分的推理。
- 机械、低风险、边界清晰且容易验证的任务，可以使用更轻量的模型与推理强度。
- 只有任务可独立推进、职责清晰且写入范围不冲突时才使用多 agent。
- 为子 agent 明确目标、负责范围、输入、预期产物和验收标准；修改代码时避免覆盖其他 agent 或用户的改动。
- 遵循当前宿主的指令优先级；项目文档和 skill 不增加权限或扩大任务范围。已有明确且覆盖当前动作的授权直接沿用，只有范围不清或出现新增授权需求时才询问。
- 使用中文交流和回复。
- 文档使用中文 Markdown 格式。
- 默认使用 jj colocated git 管理当前仓库。首次接入或需要版本控制写入时，若没有 `.jj/`，执行 `jj git init --colocate`；只读审查不初始化仓库。
- 需要执行 jj 操作时先检查 `command -v jj`；缺失时安装 jj，macOS 优先使用 `brew install jj`，其他环境按已有包管理器或官方方式安装。
- 当前仓库存在 `.jj/` 后，本地版本控制操作使用 `jj status`、`jj log`、`jj diff`、`jj describe`、`jj new`、`jj bookmark` 和 `jj git push`，不要再用 `git add`、`git commit`、`git stash` 或 `git checkout` 管理本地变更。
- 按功能领域拆分中文 change 描述，避免把无关文件混进同一个提交。
- 推送或同步主线时，先确认项目实际主线名称，再同时核对远端 bookmark 和默认工作区状态。
- 处理子目录任务前，读取其中存在的 `AGENTS.md`、`CLAUDE.md` 或 README；缺失时继承适用的上级规则，已读且未变化的内容可复用。
- 跨仓搜索默认只读；除非任务明确要求，不修改兄弟仓或外部项目文件。

- 正式版本默认使用语义化版本 `MAJOR.MINOR.PATCH`：不兼容变更提升 MAJOR，向后兼容功能提升 MINOR，向后兼容修复提升 PATCH；项目已有更严格版本规则时，以项目明确记录的规则为准，不能静默混用口径。
- 同一制品或组件的版本号必须在清单、运行时元数据、锁文件和发布标签等权威位置保持一致；CLI、内容源、模块与上游是独立版本轴。无法同轮更新的派生位置要在发布说明中列为已知差异。
- 每次正式发布必须新增 `release-notes/v<MAJOR>.<MINOR>.<PATCH>.md` 并更新 `release-notes/README.md`；索引为 AgentPhilosophy layered 输出时，更新 `.agents/custom/release-notes/README.custom.md` 后执行同步，不直接修改托管结果。
- 发布说明至少记录变更摘要、兼容性与迁移、验证结果、回滚入口和发布回执；测试通过、构建完成或候选环境 Ready 不能称为已发布，只有目标平台的 tag、Release、制品或部署回执闭环后才能下发布结论。

## 工程规范

- 新增、迁移或沉淀长期文档时，必须同步更新主入口、相关目录索引（例如 `docs/README.md`）或 `.agents/custom` 中的 layered custom 源，避免正文无入口。
- 删除或退役文档、代码、测试等内容时，直接移除失效内容，同步修正入口、索引和引用，不用“已删除 xxx”、空壳或跳过测试占位。统一退役文档只记录退役对象/原路径与可追溯的完整删除 Git 提交 SHA；删除内容和原因通过版本控制查看，不复制旧内容或另建逐次归档。
- 涉及领域模型时先明确实体、值对象、聚合和边界上下文。
- 不为技术便利跨越领域边界共享内部状态。
- 编写测试前读取 `spec/TestStrategy.md` 的“编写测试注意事项”，按业务合同验证可观察结果，避免耦合内部实现。
- 完成前必须运行最新验证命令，不能用旧日志或推测替代。
- 用户流程变更先写 BDD 验收场景，再实现代码；测试描述以 `user` 开头，采用 Given / When / Then，覆盖成功路径和关键失败路径。
- BDD 断言应面向行为结果，不绑定内部实现细节。

- 先区分终端用户界面、开发者集成文档与内部诊断。普通用户界面只表达对象、状态、影响和下一步，内部对象先映射为产品状态。
- SDK README、CLI 帮助和公开 API 文档可以准确说明完成集成需要的公开接口、依赖名称、认证方式及参数；不得暴露凭据值、内部拓扑或敏感调试数据。
- 具体产品的术语限制由该项目的受众合同或 custom 规范维护，通用规则见 `spec/ProductCopySpec.md`。
- 中英文按相同受众边界检查；用户流程或文案边界修复补充 unit、e2e 或 BDD 守卫，断言实际渲染结果。

## 项目扩展

项目特有内容应放在 `.agents/custom`，避免中央同步覆盖手写规则。

## Agent 导航入口

- Matt skills 项目级 setup、issue、triage、领域资料与明确排除项统一从 `docs/agents/README.md` 进入。
- 中央内容维护先读 `docs/agents/maintenance.md`，CLI 操作按 `docs/cli-usage-for-llm.md` 的任务入口读取相关章节。
- 修改中央 `modules/`、`presets/`、`templates/` 或项目 custom 源，通过 `scripts/sync-packaged-source.py --apply` 刷新包内镜像，再用同步 CLI 更新本仓生成结果；不手改托管 AGENTS、skills 或 state。
- 本仓验证入口：`uv run --locked ruff check .`、`uv run --locked pytest -q`、`uv run --locked sync.py validate`。完整长期文档索引是 `docs/README.md`。
- 仓库日常维护使用 `loop-check`；具体检查项、授权范围和触发方式见 `.agents/custom/loop-check.md`。
