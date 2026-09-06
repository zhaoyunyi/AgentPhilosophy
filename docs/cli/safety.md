## 十九、安全边界

- `push` 不带 `--apply` 时不写目标项目文件；`--dry-run` 是推荐显式写法。
- `push --apply` 也不会覆盖未托管的既有文件；遇到冲突会写候选文件到迁移目录。
- `adopt` 不修改目标文件内容，只把当前文件 hash 写入 `.agents/agentphilosophy-state.yaml`。
- `migrate` 只写 `.agents/migration/` 下的报告和候选文件。
- `push --prune-managed` 只清理 state 中登记、当前 hash 仍匹配、且已从当前配置输出中移除的托管文件；文件有手动改动时会拒绝清理。
- `migrate --write-config` 若可用，只能在正式 `.agentphilosophy.yaml` 不存在时写入；存在时必须拒绝覆盖。
- 不要把 `.agents/migration/proposed.agentphilosophy.yaml` 当成正式配置；`push` 只读取项目根目录 `.agentphilosophy.yaml`。
- 修改 `modules` 后必须重新运行 `validate` 和 `push --dry-run`。
