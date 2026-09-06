## 一、运行前提

- 默认在 AgentPhilosophy 仓库根目录运行命令。
- 使用 `uv run sync.py ...` 调用当前源码。
- 如果已经安装 CLI，也可以使用 `agentphilosophy-sync ...`。安装后的 CLI 在当前目录不是中央规范源时，会自动使用包内规范源。
- 命令是否可用以 `uv run sync.py <command> --help` 为准；不要把设计文档里的未来能力当成当前可执行参数。
- 如果从其他目录调用，使用全局参数指定中央源：

```bash
uv run --project /path/to/AgentPhilosophy /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy validate
uv run --project /path/to/AgentPhilosophy /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy push /path/to/project --dry-run
```

安装 CLI 后的等价入口：

```bash
agentphilosophy-sync validate
agentphilosophy-sync llm-usage
agentphilosophy-sync llm-usage --mode auto-config
agentphilosophy-sync llm-usage --mode user-breakpoints
agentphilosophy-sync llm-usage --mode user-breakpoints --format json
agentphilosophy-sync init /path/to/project --preset fullstack
agentphilosophy-sync push /path/to/project --dry-run
```
