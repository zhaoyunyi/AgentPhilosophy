---
name: prototype
description: 用可丢弃的可运行原型回答一个设计问题；适用于状态、业务逻辑或界面方向无法仅靠讨论确定时。
---

# Prototype

改编自 Matt Pocock 的 `prototype` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/prototype

目标是学习，不是交付生产代码。

1. 把问题压缩成一个可判定命题，并写明成功信号。
2. 逻辑或状态问题读取 [LOGIC.md](LOGIC.md)；界面问题读取 [UI.md](UI.md)。
3. 在临时目录或项目明确的 scratch 目录创建最小原型；不得修改生产入口、迁移、发布配置或正式数据。
4. 给用户一个可运行、可观察、可切换比较的反馈入口。
5. 记录得到的结论、仍未知的点和对原问题的回答。
6. 保留结论，删除原型；只有用户明确选择某方案后，才回到 `/grill-with-docs`、`/to-spec` 或 `/implement` 重写为生产实现。

原型不得偷偷演变成 production slice，也不以原型测试替代正式验收。
