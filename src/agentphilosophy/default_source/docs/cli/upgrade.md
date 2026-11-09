# 已接入项目升级与回退

本页面向独立使用 AgentPhilosophy 的项目，无需维护者的中央 clone 或 registry。

版本边界：`check-update`、`upgrade`、`rollback` 从 **1.3.0** 开始提供，v1.2.2 不包含这些命令。安装目标以 GitHub 上已发布、可核对回执的正式稳定 Release 为准；旧用户先按主分支 README 的稳定入口安装一次 CLI。源码验证可用 `uv run --locked sync.py ...`，开发源码不自动视为稳定版。

## 给 Agent 的请求

> 升级本项目的 AgentPhilosophy 到最新正式稳定版。保留现有模块选择和项目定制，先核对发布身份与预览，兼容且无冲突时完成升级和验证；新增模块只给建议，不兼容迁移或手改冲突时说明具体影响。保留回退 ID。

Agent 应使用项目的 `agentphilosophy-sync` skill。没有该 skill 或旧版尚无升级命令时，从本页与新版稳定安装入口引导；不要让用户重跑 `init` 覆盖已有配置。

## 手动流程

以下步骤同样是 Agent 的执行协议。`PROJECT` 表示明确的目标目录；先切换到该项目后可以使用 `.`。文件重定向示例适用于 POSIX shell，其他环境可把 JSON 输出保存为同样的目标文件。

### 1. 发现并固定目标

```bash
agentphilosophy-sync --version
agentphilosophy-sync check-update --project . --format json > /tmp/agentphilosophy-target.json
```

请为并行项目选择不同的临时目标文件。先检查退出码为 0，再读取 JSON：

- `target.version` / `tag`：正式稳定版本，默认 GitHub latest Release。可用 `--version X.Y.Z` 选择特定稳定版本。
- `target.source_revision`：40 位 Git commit SHA，已与远端 tag、发布回执交叉核对。
- `target.content_version` / `source_tree_hash`：内容版本与内容清单指纹。
- `target.wheel_sha256`：已下载并与发布回执核对的 wheel 摘要。
- `target.release_url`：需要阅读的发布说明；跨多版升级也阅读中间版本的兼容性说明。
- `install_command`：固定提交的安装参数数组。
- `workflow_supported`：该目标是否提供本页事务升级命令。旧稳定版仍可查询身份，但使用其当时的安装/同步说明，不能装回旧 CLI 后继续调用新命令。

`current` 只表示所比较的 CLI 版本相同，项目是否需要同步仍由 `upgrade` 计划判断。`local_newer` 不代表应该降级。离线、GitHub 限流、缺失制品、摘要或源码身份不符均返回 `failed` 和非零退出码，状态是未知而非已是最新。

### 2. 准备匹配的 CLI

如果当前 CLI 与目标不同，执行结果中的固定提交安装命令，例如：

```bash
uv tool install --force 'git+https://github.com/zhaoyunyi/AgentPhilosophy.git@<完整提交SHA>'
agentphilosophy-sync --version
```

将占位符换成刚核对的 `target.source_revision`，不要换成 `main`。Agent 应使用已核对的参数数组，不把网络响应当成任意 shell 脚本执行。旧 CLI 的首次引导使用新稳定版 README 的固定 tag 安装命令；不要假设旧安装包支持 `check-update`。

这一步更新本机工具，不自动同步其他项目。如果需要保持本机默认 CLI，可用 `uvx --from 'git+https://github.com/zhaoyunyi/AgentPhilosophy.git@<完整提交SHA>' agentphilosophy-sync ...` 运行目标版本，后续命令保留同一前缀。

### 3. 预览项目升级

```bash
agentphilosophy-sync upgrade . --target /tmp/agentphilosophy-target.json --dry-run
```

也可加 `--format json`。CLI 会重新校验运行版本、内容源指纹、项目配置和 state，列出文件差异、冲突、退役输出与可选模块。默认使用当前安装包的内容源；运行目录若本身是中央源，或显式传入了 `--source`，其内容必须与目标指纹匹配。

已有 `modules` 是项目选择，升级不根据新版 preset 自动扩展。`optional_modules` 表示当前源中未选的模块，可结合技能指南判断用途、项目类型及依赖后再推荐，并不表示全部适合安装。

兼容检查分别比较 CLI、内容源与已选模块的语义版本。跨主版本、模块选择变化、托管输出退役/改名均需要迁移决定。缺少模块、未知版本、降级、手改冲突或尚未恢复的事务会阻断。预览失败时项目文件保持不变。

### 4. 应用并验证

```bash
agentphilosophy-sync upgrade . --target /tmp/agentphilosophy-target.json --apply --format json
```

Agent 已获用户升级授权且计划兼容、无冲突时，直接完成这一步，无需再索取相同授权。CLI 会在项目锁内重新检查计划、保存快照、应用更新并检查输出及 state。不会自动提交、推送或发布。

成功返回 `upgraded`、`upgrade_id` 和验证结果；重复执行同一已完成升级返回 `unchanged`，不重写 state 时间或再生成快照。缺少 `--apply` 时只预览。所有 `blocked` / `failed` 都使用非零退出码。

工具验证覆盖配置、托管文件与记录的一致性；不等于宿主已刷新技能或项目业务测试通过。Agent 还应按项目既有约定执行相关检查，并通过新会话的技能列表核对实际发现情况，分别报告已验证和待验证部分。

如果用户已明确决定采用列出的不兼容迁移，可在预览及应用命令中加入 `--allow-breaking`。它不跳过身份校验、文件冲突、未知版本或降级限制。移除的托管文件仅在当前内容仍等于登记值时进入可恢复删除计划。

## 冲突处理

- **托管文件有手改**：查看 diff，把长期项目规则整理到 `.agents/custom` 对应来源，再按迁移/接管合同处理。不要删除文件或手改 state 来消除冲突。
- **目标身份不匹配**：核对 CLI 路径、版本、启动目录和 `--source`；重新从固定提交准备工具。不要把目标 JSON 的 hash 改成当前值。
- **存在 pending / recovery_required 快照**：先检查对应升级 ID 并恢复，不开启第二次覆盖升级。
- **全局工具较新而项目较旧**：项目可保留旧内容。`status` 是与当前本地源比较，`check-update` 才会查询正式发布；二者结论的比较对象不同。

## 回退与中断恢复

```bash
agentphilosophy-sync rollback . --id <升级ID> --dry-run
agentphilosophy-sync rollback . --id <升级ID> --apply --format json
```

回退仅恢复该次升级涉及的文件内容、权限和原 state，删除本次新增文件，保留无关 WIP。不依赖旧安装包或旧内容源，不修改 Git/jj 历史，也不降低本机 CLI 版本。回退后如需旧版工具，按旧正式 Release 的固定身份另行安装。

快照保存在 `.agents/upgrades/<升级ID>/receipt.json`，包括恢复所需文件内容。目录内的忽略规则避免正常 Git 提交收集快照，但不要用强制添加发布它。快照保留直到项目维护者确认不再需要回退；不要在升级尚未验收时清理。

写入异常会尝试自动恢复，返回 `failed` 和 `recovery`。`failed_recovered` 表示本次文件已恢复；`recovery_required` 表示需要检查后再执行回退。进程意外退出可能留下 `pending`，通过同一回退入口恢复。锁由操作系统持有，进程退出会释放；保留的 `.lock` 文件本身不表示正在运行。

升级后又手改了受影响文件时，回退在写入前整体拒绝并指出冲突；先保存、审阅这些改动再处理。重复回退返回 `already_rolled_back`。空的新增目录可能保留，不影响文件恢复。

## 完成报告

报告旧/新 CLI 和内容版本、固定源码提交、已更新模块、可选模块建议、升级 ID、文件验证结果，以及项目测试/宿主发现是否完成。失败报告具体原因和恢复状态，不使用“已升级成功”概括部分完成。

维护者需要遵守 [发版流程](../release-process.md) 的兼容声明与制品回执合同。自定义源、预发布和 `main` 使用显式源码同步流程；本页的自动升级只针对正式稳定 Release，不把开发内容包装成稳定发布。
