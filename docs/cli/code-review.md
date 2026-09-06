## 十、独立 code-review 审查 skill

当前中央源提供可选模块 `skill-code-review`。该模块会同步生成 `skills/code-review/SKILL.md` 和 `.agents/skills/code-review/SKILL.md`，用于让依赖项目快速载入 `/code-review` 双轴审查流程，而不必同步完整 Matt Pocock 产品工程主线。

`skill-code-review` 与 `skill-mattpocock-engineering` 写入同一个 `code-review` skill 路径，不能同时启用。已有项目如果已经启用 `skill-mattpocock-engineering`，说明它已经拥有 `code-review`；只有当项目只需要审查入口、不需要 `/grill-me`、`/grill-with-docs`、`/to-spec`、`/to-tickets`、`/implement` 和 `/tdd` 时，才追加 `skill-code-review`。

```yaml
modules:
  - existing-module
  - skill-code-review
```

随后执行标准同步流程：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

同步后验证：

```bash
find -L /path/to/project/.agents/skills/code-review -name SKILL.md -print
find -L /path/to/project/skills/code-review -name SKILL.md -print
```
