## 九、架构加深评审 skill

当前中央源默认 preset 会包含 `skill-improve-codebase-architecture`。该模块会同步生成 `skills/improve-codebase-architecture/SKILL.md` 和 `.agents/skills/improve-codebase-architecture/SKILL.md`，用于让 agent 在用户要求改进架构、寻找重构机会、合并紧耦合模块、提高可测试性或让代码库更容易被 agent 导航时，先做只读架构评审报告。

该 skill 改编自 Matt Pocock 的 `improve-codebase-architecture`（MIT License），但已经按 AgentPhilosophy 的项目愿景收口：

- 先读取项目 `AGENTS.md`、README、`spec/ArchitectureSpec.md`、`spec/DDDSpec.md`、`spec/BDDSpec.md`、`GLOSSARY.md` / `GLOSSARY-MAP.md` 和 `docs/adr/`。
- 把候选重构解释成 Module、Interface、Implementation、Depth、Seam、Adapter、Leverage、Locality 等统一架构语言。
- 第一阶段只输出临时目录里的 HTML 候选报告，不在用户选择前直接改代码。
- 用户选择候选后才进入接口设计、BDD/TDD 和实现。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动向旧配置追加新模块。需要让旧项目拿到该 skill 时，把模块追加到现有 `modules`，不要替换已有模块：

```yaml
modules:
  - existing-module
  - skill-improve-codebase-architecture
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
find -L /path/to/project/.agents/skills/improve-codebase-architecture -name SKILL.md -print
find -L /path/to/project/skills/improve-codebase-architecture -name SKILL.md -print
```
