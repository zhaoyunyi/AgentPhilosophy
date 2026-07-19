# Triage 标签

| 规范角色 | 当前 tracker 标签 | 含义 |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 等待维护者评估 |
| `needs-info` | `needs-info` | 等待报告者补充信息 |
| `ready-for-agent` | `ready-for-agent` | 信息完整，可由 agent 实现 |
| `ready-for-human` | `ready-for-human` | 需要人工判断或发布操作 |
| `wontfix` | `wontfix` | 本次不处理 |

创建前先读取远端现有标签并优先复用等价语义。`ready-for-agent` 不代表已授权发布新版本或批量修改依赖项目。
