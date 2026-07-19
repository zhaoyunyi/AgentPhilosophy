# Issue Tracker：GitHub

使用 `origin` 指向的 [zhaoyunyi/AgentPhilosophy](https://github.com/zhaoyunyi/AgentPhilosophy) GitHub Issues。先从 remote 复核仓库，再使用 `gh`。

- 读取：`gh issue view <number> --comments`
- 列表：`gh issue list --state open --json number,title,body,labels,comments`
- 创建：`gh issue create --title "..." --body "..."`
- 评论：`gh issue comment <number> --body "..."`
- 标签：`gh issue edit <number> --add-label "..."`
- 关闭：`gh issue close <number> --comment "..."`

Wayfinder map 使用 `wayfinder:map`；优先使用 sub-issues、native dependencies 和 assignee。不可用时双向记录 `Part of #<map>` 与 `Blocked by:`。
