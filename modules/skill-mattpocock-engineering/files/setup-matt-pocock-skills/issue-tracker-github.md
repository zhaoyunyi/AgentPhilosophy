# Issue Tracker：GitHub

使用项目已有 GitHub Issues 与 `gh` CLI。先从 remote 确认仓库，不在命令中猜 owner/repo。

## 基本操作

- 读取：`gh issue view <number> --json number,title,body,labels,comments`
- 列表：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`
- 创建：`gh issue create --title "..." --body "..."`
- 子 issue：优先使用 `gh issue create --parent <parent>` 或 `gh issue edit <parent> --add-sub-issue <child>`；旧版用 API 传 database id。
- 阻塞：优先使用 `gh issue create --blocked-by <n>,<n>` 或 `gh issue edit <child> --add-blocked-by <blocker>`；旧版用 dependencies API 的 blocker database id。
- 评论：`gh issue comment <number> --body "..."`
- 标签：`gh issue edit <number> --add-label "..."`
- 关闭：`gh issue close <number> --comment "..."`

写入前用 `gh repo view --json nameWithOwner` 确认目标是用户自己的仓库，不要把 issue 写入 `mattpocock/skills` 上游仓库。

Pull requests 默认不进入 triage；若本项目明确把外部 PR 当需求入口，在这里记录筛选规则。

## Wayfinder

- map 使用 `wayfinder:map` 标签。
- 子票优先使用 GitHub sub-issues；不可用时在 map task list 与子票 `Part of #<map>` 双向记录。
- 阻塞优先使用 native issue dependencies；不可用时用 `Blocked by:`。
- claim 通过 assignee 表示；frontier 是 map 下未关闭、无开放 blocker、无 assignee 的子票。
- 解析依赖 API 时使用 issue database id，不把 issue number 或 node id 混用。
