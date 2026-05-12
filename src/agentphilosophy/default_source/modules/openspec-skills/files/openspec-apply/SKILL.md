---
name: openspec-apply
description: 按已批准 OpenSpec change 执行实现、测试和收尾。
---

# OpenSpec Apply

执行要求：

- 先读取 proposal、tasks、design 和受影响 spec。
- 每完成一项任务就运行对应验证。
- 归档前必须执行 strict validate，并确认代码实现与 spec 无漂移。
