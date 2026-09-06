---
name: resolving-merge-conflicts
description: 按双方修改意图逐块解决正在进行的 jj、merge 或 rebase 冲突，并完成原操作；适用于用户提到冲突、conflict、merge 或 rebase 卡住。
---

# Resolving Merge Conflicts

改编自 Matt Pocock 的 `resolving-merge-conflicts` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/resolving-merge-conflicts

1. 先识别版本控制系统。存在 `.jj/` 时读取项目 jj 规则，使用 `jj status`、`jj log`、`jj diff` 和冲突标记；否则检查 Git merge/rebase 状态。
2. 固定冲突两侧的来源提交、spec、issue、测试和 change 描述，逐块解释双方意图。
3. 根据意图合并行为，不机械选择 ours/theirs，不顺手改无关文件。
4. 每解决一组冲突就运行最小相关验证；全部完成后运行项目完整验证。
5. 完成原来的 jj/Git 操作并确认状态干净。除非用户明确要求放弃，持续完成冲突解决，不默认 abort。

若两侧意图真正互斥且无法从证据确定，列出具体冲突和影响后只向用户询问该决策。
