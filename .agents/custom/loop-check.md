# AgentPhilosophy 巡检计划

## 范围与执行方式

- 仓库：AgentPhilosophy；实际主线 `main`。每轮读取当前 jj revision、远端和 WIP。
- 授权：本次用户要求直接修改并提交 PR，不等待逐项审批或查阅；在下列检查项涉及的本仓中央源、文档、测试和生成结果内修复、验证、提交 PR。不得据此扩大到依赖项目、正式发布或合并 PR。
- 权威来源：`modules/`、`presets/`、`catalog.yaml`、`.agents/custom/`；包内镜像用 `scripts/sync-packaged-source.py` 更新，托管输出/state 用同步 CLI 更新。
- 触发：每日候选与相关变更事件；当前未注册定时任务或事件 hook。手动调用及 agent 主动选择可执行本计划。
- 单轮预算：默认 30 分钟，优先处理变更相关项；完整检查未完成时保留未解决项，不推进完整基线。每周候选执行一次全量复核，仍需真实调度调用。
- 隔离与去重：先检查当前任务/进程和同检查 ID、同根因的开放 PR；已有 WIP 或并行任务时使用隔离 jj 工作区，不覆盖默认工作区。没有互斥机制时在 Git 公共目录内建立仓库运行锁，记录进程和执行身份，退出后释放；异常退出先确认持有者状态。
- 当前结果：优先沿用任务回执与 PR，需跨轮保存时维护 `.agents/loop-check-state.md` 的当前摘要；不保存逐日无变化报告。该文件首次实际巡检后创建，不写虚构基线。
- 统一退役索引：`docs/retirements.md`，首次实际删除后创建并加入 `docs/README.md`；本次新增技能不产生退役条目。

## 检查项

| ID | 触发与范围 | 检查方法与通过标准 | 修复与复查 |
| --- | --- | --- | --- |
| LC-REUSE | 每日变更；新增模块/资源 | 对照 `catalog.yaml`、`modules/*/module.yaml`、`src/agentphilosophy/` 现有公开能力与调用；新模块无同职责重复 owner、无输出碰撞，不跨领域强行复用 | 修改实际中央源或调用；运行相关测试及 `uv run --locked sync.py validate` |
| LC-DOCS | 每日变更；CLI/规则/索引变化 | 对照 `docs/cli/`、README、真实 CLI 和 `docs/README.md`；检查 `uv run --locked sync.py llm-usage` 输出与相关测试，所有长期文档可达且示例反映实现 | 修正正文、CLI include 与索引；复跑相关测试、完整文档索引校验 |
| LC-MIRROR | 每日；模块/模板/custom 变化 | `python3 scripts/sync-packaged-source.py --check`、`uv run --locked sync.py validate`、`uv run --locked sync.py validate .`、`uv run --locked sync.py status --project .`；镜像与源一致，无手改托管漂移 | 更新源后刷新镜像，`push . --dry-run` 检查范围再 `push . --apply`，回读 status 与双目标输出 |
| LC-RETIRE | 迁移/替换/删除后；每周复核剩余项 | 从本轮差异确定旧路径/能力，用引用、调用和测试证据验证替代路径及消费者；同步工具的历史兼容行为仍有用户时保留 | 删除已确认失效内容及引用，保留有效行为测试；运行受影响用例，按 skill 规则记录删除 SHA |
| LC-TESTS | 行为/测试变化后；每周全量 | 按 `spec/TestStrategy.md` 检查行为覆盖、skip/xfail 理由；`uv run --locked ruff check .`、`uv run --locked pytest -q`、`uv run --locked sync.py validate` 全部通过 | 修复根因和有业务意义的测试，保留原失败证据，不删验收路径换绿测 |
| LC-EVIDENCE | PR、CI、部署或业务状态变化后 | 绑定当前 revision 和当前执行结果，分开记录 `repo-local`、`deployed`、`business-verified`；绿测、Ready、健康接口或合并状态不能越级 | 补取缺失层级的当前证据，不能把历史回执、空 Store/日志或旧 issue 当成现状 |
| LC-WORKSPACE | 每日开始与准备清理时 | 检查 jj/Git 主线、远端 bookmark、默认工作区、未提交 WIP、进程、子仓库、恢复价值和敏感文件；不按年龄或名字猜测可删 | 只在范围、祖先覆盖、依赖、进程和恢复检查完成后清理；保护 active/conflicted/non-empty/recovery-bearing 对象 |
| LC-RELEASE | 版本改动/发布前后 | 对照 `docs/release-process.md`、模块版本、CLI/内容独立版本轴与当前回执；未发布内容不冒充已发布，目标项目安装与宿主发现分层 | 修正本仓元数据/说明并验证；发布动作不在此计划授权内 |

失败按代码、环境或缺证据分类；只有完成的检查写通过。无可行动变化不重复开 PR 或发通知。其他候选（运行时幂等、生产缓存等）不因本计划存在而自动启用。
