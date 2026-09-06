## 十七、新项目接入流程

1. 选择 preset。
2. 生成 `.agentphilosophy.yaml`。
3. 校验目标项目。
4. 先 dry-run，确认没有冲突。
5. 再 apply。
6. 最后查看状态。

```bash
uv run sync.py init /path/to/project --preset fullstack
uv run sync.py validate /path/to/project
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
uv run sync.py status --project /path/to/project
```

如果需要交互确认项目名、项目类型、描述或测试命令，使用：

```bash
uv run sync.py init /path/to/project --interactive
```
