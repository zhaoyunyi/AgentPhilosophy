# Issue Tracker：GitLab

使用项目已有 GitLab Issues 与 `glab` CLI。先从 remote 确认仓库。

## 基本操作

- 读取：`glab issue view <number> --comments`
- 列表：`glab issue list -F json`
- 创建：`glab issue create --title "..." --description "..."`
- 评论：`glab issue note <number> --message "..."`
- 标签：`glab issue update <number> --label "..."`
- 关闭：先 note 说明，再 `glab issue close <number>`。

Merge requests 默认不进入 triage；需要时在这里记录外部贡献者筛选规则。

## Wayfinder

- map 使用带 `wayfinder:map` 标签的 issue；子票写 `Part of #<map>`。
- 阻塞优先使用 GitLab native blocking link；不可用时用 `Blocked by:`。
- claim 使用 assignee；frontier 是未关闭、无开放 blocker、无 assignee 的子票。
