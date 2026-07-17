# Issue Tracker：本地 Markdown

issue 与 spec 保存于 `.scratch/`：

- 功能目录：`.scratch/<feature-slug>/`
- spec：`.scratch/<feature-slug>/spec.md`
- ticket：`.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始，每票一个文件。
- 状态：文件头部 `Status:`；依赖：`Blocked by:`；讨论追加在 `## Comments`。

## 发布与读取

- “发布 spec”表示创建或更新该功能的 `spec.md`。
- “发布 ticket”表示在 `issues/` 新建独立文件。
- 用户应传入 ticket 路径；未传时只在当前功能目录内发现，不跨项目猜测。

## Wayfinder

- map：`.scratch/<effort>/map.md`。
- 子票：`.scratch/<effort>/issues/<NN>-<slug>.md`，含 `Type:`、`Status:`、`Blocked by:`。
- frontier：所有未解决、未被阻塞、未认领的子票，按编号取最前。
- claim：先把 `Status:` 改成 `claimed`。
- resolve：在 `## Answer` 写结论，状态改为 `resolved`，并在 map 的 `Decisions so far` 增加带路径摘要。
