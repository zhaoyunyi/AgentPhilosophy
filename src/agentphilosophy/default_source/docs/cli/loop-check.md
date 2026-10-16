# Loop-Check 仓库巡检

默认四类 preset 包含 `skill-loop-check`，模块初始版本为 `1.0.0`。它将 `loop-check`、检查候选、计划指引和调用 metadata 同步到 `skills/loop-check/` 与 `.agents/skills/loop-check/`，支持 agent 在迁移、替换和维护任务中主动选择。

首次调用时根据当前仓库规则、目录、测试和历史问题生成项目自有计划，默认路径为 `.agents/custom/loop-check.md`；以后同步技能不会覆盖它。清单为每项确定范围、证据、命令/步骤、通过标准、每日或事件触发方式、修复与验证方法。复用、文档代码一致性、迁移残留是主要候选；测试有效性、规则 owner、生成物、版本发布、证据层级、WIP/缓存、幂等恢复和敏感信息按项目适用性选择。

已有项目的模块列表保持显式冻结；需要启用时在 `.agentphilosophy.yaml` 的 `modules` 中追加 `skill-loop-check`，沿用标准流程：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
agentphilosophy-sync status --project /path/to/project
```

调用示例：

```text
使用 $loop-check 为当前仓库建立每日和迁移后检查清单。
允许在本仓范围内直接修复、验证并提交 PR，不用逐项等审批。
```

这会生成并执行适用计划；定时运行仍需要用户要求启用后由实际 CI/宿主调度器登记。描述中的每日或主动触发能力不代表已部署常驻进程、hook 或自动化。本仓计划位于 [.agents/custom/loop-check.md](../../.agents/custom/loop-check.md)，当前没有因安装技能而注册定时任务。

已有授权直接沿用，发现问题后完成修复、复查和 PR，不人为增加查阅/批准关卡。用户只要求只读检查时保持只读；安装或隐式发现技能不自动授予写入权限。保留 WIP，同根因复用现有 PR，持续无改善或预算耗尽则留下剩余项，未验证不冒充通过；创建 PR 不代表允许合并、部署或修改生产数据。

退役删除同时处理实现、文档、专属测试、配置和引用，保留仍有效的行为测试与尚未完成迁移的消费者。原位置不留占位或旧内容副本。统一退役文档只记对象/原路径与完整删除 Git 提交 SHA：先固定删除提交，后续提交登记；若 squash/rebase 改写历史，则以实际合入 SHA 回填验证，不能让索引依赖将被清理的临时历史。没有实际退役时不生成空退役记录。

自动化验收覆盖四种 preset 的双目录安装、隐式发现 metadata、完整支持文件，以及自有计划和同名自有技能保护。这些验证不代替宿主实际发现、定时执行和真实仓库巡检效果的验收。
