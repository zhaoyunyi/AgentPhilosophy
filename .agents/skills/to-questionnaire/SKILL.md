---
name: to-questionnaire
description: 把用户无法独立回答的决策整理成给特定知情人的 Markdown 问卷。
disable-model-invocation: true
---

# To Questionnaire

改编自 Matt Pocock 的 `to-questionnaire` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/productivity/to-questionnaire

访谈“发送方式”，不要访谈用户本来就不知道的主题事实。

1. 确认收件人的角色、专业背景、与用户的关系，以及对方掌握而用户缺少的知识。
2. 确认用户必须从回复中获得的具体事实或决定，以及答案将用于什么后续动作。
3. 在当前目录写入 `to-questionnaire-<slug>.md`。问题按重要性排序，多于少量问题时按主题分组。
4. 每个问题只问一件事；容易被误解时补一行“为什么重要”；紧接着提供可填写的引用块。
5. 覆盖用户在第 2 步列出的每个缺口，并加入“还有什么是我们没有问到但应该知道的？”作为收尾。

问卷必须包含目的、发送方、接收方、答案用途、必要背景、回答方式和截止要求。允许部分回答与“不知道”，避免强迫收件人猜测。
