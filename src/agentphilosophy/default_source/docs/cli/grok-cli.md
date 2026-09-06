## 十五、Grok CLI headless 编排 skill

当前中央源默认 preset 包含 `skill-orchestrate-grok-cli`，同步后同时提供：

```text
skills/orchestrate-grok-cli/
.agents/skills/orchestrate-grok-cli/
```

该 Skill 用于把多个 Grok CLI 当作受限执行者编排，覆盖单次 headless 入口、自动批准、Stop hook、并行隔离、进程轮询和独立 diff 审查。一次性任务使用 `grok --prompt-file`、`--prompt-json` 或 `-p`；`grok agent headless` 是 WebSocket relay，不作为 prompt 执行入口。

已有项目的 `modules` 是显式冻结的。需要该能力时追加模块并执行标准同步流程：

```yaml
modules:
  - existing-module
  - skill-orchestrate-grok-cli
```

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
find -L /path/to/project/{skills,.agents/skills}/orchestrate-grok-cli -type f -print
```

自动批准只消除 Grok 自身的交互确认，不扩张用户授权；生产、外部写入、凭据、提交、推送和发布仍受原始任务边界约束。Stop hook 只提供完成信号，最终验收必须由编排者基于现场 diff 和新鲜验证独立完成。
