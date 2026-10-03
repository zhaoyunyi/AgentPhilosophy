---
name: pr
description: 编写 PR 正文；适用于创建或更新 pull request 描述，需要说明改动、前后验证证据、回滚成本和影响范围时。
metadata:
  credits:
    skill: show-me
    author: Dex Horthy
    organisation: Humanlayer
    url: "https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md"
---

# PR

改编自 Matt Pocock 的 `pr` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/pr
原始表达方法的归属见 [CREDITS.md](CREDITS.md)。

目标：让未读过会话的 reviewer 理解最终改动、验证证据和合入影响。使用 `GLOSSARY.md` 中的领域语言，遵循仓库 PR 模板与当前用户要求。

## 正文

```markdown
## 摘要

<具体问题与改变后的行为，必要时配最小图、diff 或树>

## 证据

- 修改前：<症状、失败测试、输出或截图>
- 修改后：<同一场景的通过测试、输出或截图>

## 合入影响

- 可逆性：<能否直接回滚，以及需要的恢复动作>
- 影响范围：<调用方、数据、流程或平台>
```

- 用最小视图解释实际问题：算法用伪代码，调用顺序用调用树，目录职责用浅层文件树，组件交互用 Mermaid，局部变化用 diff。简单修改用一两句话即可。
- 证据绑定同一行为场景和实际执行结果；界面修改可用前后截图，非视觉修改优先使用测试或命令输出。缺失证据明确写出，不能捏造。
- 描述回滚是否可恢复原行为，以及迁移、删除或外部副作用是否需要额外恢复。具体说明哪些用户、调用方和状态会受影响。
- PR 范围变化后重写标题和正文，使其反映最终实现。只保留帮助 reviewer 判断的技术与验证信息。

本 skill 负责正文写作；创建、更新或发布 PR 按当前任务授权执行。
