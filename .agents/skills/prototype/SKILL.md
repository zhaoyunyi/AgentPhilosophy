---
name: prototype
description: 用可丢弃的可运行原型回答一个设计问题；适用于状态、业务逻辑或界面方向无法仅靠讨论确定时。
---

# Prototype

改编自 Matt Pocock 的 `prototype` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/prototype

目标是用可运行的一手证据回答一个设计问题，不是交付生产代码。

1. 把问题压缩成一个可判定命题，并写明成功信号。
2. 逻辑或状态问题读取 [LOGIC.md](LOGIC.md)；界面问题读取 [UI.md](UI.md)。
3. 逻辑或状态问题优先生成一个无需构建和服务端的自包含 HTML 文件，让非开发者可以直接打开、自由操作并按引导场景验证；界面方向问题优先在现有真实页面的隔离分支用 variant 切换比较，具体读取 [UI.md](UI.md)。
4. 在隔离 workspace、临时目录或项目明确的 scratch 目录创建最小原型；不得修改生产迁移、发布配置或正式数据，界面 variant 必须有 production guard。
5. 记录得到的结论、仍未知的点和对原问题的回答。
6. 把原型作为一手证据保留在独立的 `prototype/<name>` jj bookmark 或 Git branch，并在 issue/spec/ADR 中留下指针；主线只接收验证后的结论，不直接合入原型实现。
7. 只有用户明确选择某方案后，才回到 `/grill-with-docs`、`/to-spec` 或 `/implement` 重写为生产实现。

原型不得偷偷演变成 production slice，也不以原型测试替代正式验收。需要清理时先确认指针和结论已经持久化，不默认删除仍承担证据作用的 prototype branch。
