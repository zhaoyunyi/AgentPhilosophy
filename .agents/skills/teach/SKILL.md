---
name: teach
description: 在当前工作区围绕一个长期目标分多次会话教学，并持续记录使命、资源、课程和学习进展。
disable-model-invocation: true
argument-hint: "你想学习什么？"
---

# Teach

改编自 Matt Pocock 的 `teach` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/teach

这是跨会话、带状态的教学请求。

## 工作区

- 当前目录本身就是专用学习仓库时，沿用上游根目录布局。
- 当前目录是产品/代码仓时，默认放到 `.scratch/learning/<topic>/`，避免污染生产目录。
- 用户明确要求团队长期共享时，使用 `docs/learning/<topic>/`，并更新 `docs/README.md`。

工作区包含：

- `MISSION.md`：为什么学、能用来做什么，格式见 [MISSION-FORMAT.md](MISSION-FORMAT.md)。
- `RESOURCES.md`：高可信资源与用途，格式见 [RESOURCES-FORMAT.md](RESOURCES-FORMAT.md)。
- `learning-records/NNNN-<slug>.md`：关键理解、误区与能力证据，格式见 [LEARNING-RECORD-FORMAT.md](LEARNING-RECORD-FORMAT.md)。
- `lessons/NNNN-<slug>.html`：一次只教一个紧凑目标的课程。
- `reference/*.html`：可打印的速查表、算法、语法或 glossary。
- `assets/`：课程复用的样式、测验、模拟器和组件。
- `NOTES.md`：教学偏好和临时观察。

## 教学原则

1. 先确认 mission；mission 改变时先征得用户同意并写学习记录。
2. 知识来自高可信来源，不把模型记忆当唯一证据。
3. 每节课只提供一个可感知的小胜利，落在用户的最近发展区。
4. 先给必要知识，再用立即反馈的练习形成技能。
5. 使用检索练习、间隔与交错提高长期保持，不以当场流畅误判掌握。
6. 课程复用 `assets/`，不在每个 HTML 内重复可共享组件。
7. 每节课包含一个主要来源、练习反馈和继续提问入口；完成后更新学习记录。
8. 需要真实经验时推荐可信社区或实践场景；尊重用户不参与社区的选择。

开始新会话前读取 mission、最近学习记录、资源和已有资产，再决定下一节课，而不是从头重讲。
