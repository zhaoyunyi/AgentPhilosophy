# 测试套件治理与精简 skill

中央源将用户提供的 `test-suite-pruning-skill` 附录整理为中文规范和项目级 skill，保留原有决策案例、图标、默认提示及自动发现策略。规范与执行流程通过现有同步机制分发，不需要安装额外测试工具。

## 分发内容

| 模块 | 输出与职责 |
| --- | --- |
| `spec-test-general` | `spec/TestStrategy.md` 的测试套件治理原则，以及 `AGENTS.md` 中的规范入口；路径跟随 `paths.spec_dir` |
| `skill-test-suite-pruning` | `skills/test-suite-pruning/` 和 `.agents/skills/test-suite-pruning/` 下的完整 skill、案例、图标和调用配置；路径跟随 `skill_targets` |

四类默认 preset 均包含这两个模块。skill 可独立安装；同时选择规范模块时，生成的测试规范和 `AGENTS.md` 会链接到实际配置的 skill 目录。只选择测试规范时仍可获得完整治理原则，不生成不存在的 skill 文件入口。

使用安装包的项目，先按 [升级指南](upgrade.md) 核对所选正式 Release 是否包含这些模块，再更新 CLI 与项目内容。源码验收可显式选择已包含这些模块的中央目录；源码文件存在不等于对应版本已发布。

## 已接入项目更新

旧项目的 `modules` 列表是显式冻结的。升级 CLI 或内容源会刷新已选模块，但不会自动追加新模块：

1. 已有 `spec-test-general` 的项目，正常同步就会更新测试规范。
2. 首次采用 skill，在原有 `.agentphilosophy.yaml` 的 `modules` 列表中追加 `skill-test-suite-pruning`；缺少测试规范时，一并追加 `spec-test-general` 和它要求的 `doc-templates`。保留其他模块、目录、变量与项目 custom。
3. 预览与应用后检查双目标的四个资源及规范入口。以后保留所选模块即可通过正常同步持续更新它们。

使用已经包含本次内容的源码，在中央仓库根目录执行：

```bash
uv run --locked sync.py validate /path/to/project
uv run --locked sync.py push /path/to/project --dry-run
uv run --locked sync.py push /path/to/project --apply
uv run --locked sync.py status --project /path/to/project
```

安装版包含这些模块后，可用 `agentphilosophy-sync` 执行相同子命令。调用时持续使用同一内容源；只升级安装包不等于项目托管文件已同步。若已存在同名自有 skill 或手改托管文件，按现有冲突报告核对后处理，不覆盖自有内容或强制重建配置。保留显式旧 `.codex/skills` 或自定义 `.claude/skills` 路径，不借此迁移目录。

## 调用与规则

```text
使用 $test-suite-pruning 审查这次功能删除涉及的测试，判断哪些保留、合并、改写、删除或仅作一次性验收，并记录行为依据、验证结果和剩余风险。
```

核心判断：保护当前高风险合同；删除无剩余合同的退役能力专属测试；区分一次性清理检查和仍有效的安全、兼容、迁移负向合同；按输入、断言、边界和失败模式判断重复。覆盖率和耗时都是辅助证据，不是删测试的单独理由；不能为变绿而跳过或削弱断言。

`optimize-build-pipeline` 负责执行效率与资源问题，本 skill 负责测试保护的去留。仅要求 CI 提速时，不自动扩展为测试删减。仅评审时产出决策；明确授权清理时才实施。安装 skill 不会执行清理、发起变异测试、创建定时任务或修改其他项目。

同步成功证明文件和元数据已生成；当前会话是否发现 skill 需以宿主技能列表为准，自然语言路由效果和实际业务回归另行验收。
