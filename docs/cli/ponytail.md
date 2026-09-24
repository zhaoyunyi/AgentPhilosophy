## 七、Ponytail 精简编码 skill

Ponytail 上游仓库：https://github.com/DietrichGebert/ponytail

`skill-ponytail` 是显式可选模块，不包含在中央源默认 preset 中。项目选择该模块后，会把 Ponytail `4.10.0` 适配版的 `SKILL.md`、`agents/openai.yaml` 与 MIT 许可证同时生成到 `skills/ponytail/` 和 `.agents/skills/ponytail/`，用于让 agent 在新增功能、修 bug、重构、review、设计或选择依赖前先追踪真实调用链，再按 `lite|full|ultra` 模式判断是否真的需要写代码、能否复用代码库、标准库、平台能力或既有依赖，并避免过度工程。

本轮上游的 `skills/ponytail/SKILL.md` 与此前锁定内容一致；4.10.0 的主要变化在 Cursor、Grok Build 等插件适配。本模块仅更新来源版本，不引入全局 hook。

该模块是 AgentPhilosophy 的项目级 skill 封装，不会自动安装上游 Codex 插件或全局 hook。目标项目只要通过 AgentPhilosophy 同步拿到 `skills/ponytail` 和 `.agents/skills/ponytail`，Codex 原生 skill discovery 就能在项目内触发；如果用户明确要求使用上游插件能力，再按上游仓库说明单独安装。

Ponytail 的默认判断顺序：

1. 能不写就不写。
2. 代码库里已经有就复用。
3. 能用语言标准库就用标准库。
4. 能用框架或平台原生能力就不新增项目代码。
5. 能用项目已有依赖就不新增依赖。
6. 一行能清楚完成就不写五十行。
7. 以上都不够时才写能正确工作的最少代码。

Ponytail 不能用来削减验证、错误处理、安全、可访问性、用户可见流程、BDD/TDD 或项目已有架构边界；它约束的是“少写不必要代码”，不是降低工程标准。

已有项目的 `.agentphilosophy.yaml` 模块列表是显式冻结的；升级 CLI 不会自动追加或删除可选模块。需要安装时，把模块追加到现有 `modules`，不要替换已有模块：

```yaml
modules:
  - existing-module
  - skill-ponytail
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
find -L /path/to/project/.agents/skills/ponytail -name SKILL.md -print
find -L /path/to/project/skills/ponytail -name SKILL.md -print
```

需要卸载已安装的 Ponytail 时，从 `.agentphilosophy.yaml` 删除 `skill-ponytail`，先执行 `push /path/to/project --dry-run` 确认共享托管输出没有冲突，再执行 `push /path/to/project --apply` 刷新共享输出和模块状态。只有 apply 成功后，再执行 `push /path/to/project --prune-managed`，安全删除未被手改的两个失活托管 skill；apply 失败时不要 prune，避免形成部分卸载状态。`superpowers-system` 同样是显式可选模块；从配置删除后执行相同流程，可移除其 AGENTS 规则。
