## 四、目标项目配置

目标项目根目录使用 `.agentphilosophy.yaml` 声明配置。CLI 不从该文件读取中央源路径；中央源由当前工作目录或 `--source` 参数决定。

最小示例：

```yaml
project_name: DemoProject
project_type: mobile-sdk
preset: mobile-sdk
description: 移动 SDK 项目

paths:
  docs_guide_dir: docs/guide
  spec_dir: spec

skill_targets:
  repo_skills: skills
  codex_project: .agents/skills

modules:
  - openspec-skills
  - jj-conventions
  - model-constraints
  - doc-templates
  - multi-module-layout
  - release-conventions
  - spec-program
  - spec-ddd
  - spec-bdd
  - spec-test-mobile
  - spec-test-general
  - spec-product-copy
  - spec-architecture
  - skill-agentphilosophy-sync
  - skill-jj-management
  - skill-target-jj
  - skill-coding-standards
  - skill-repo-management
  - skill-optimize-build-pipeline
  - skill-improve-codebase-architecture
  - skill-mattpocock-engineering
  - skill-portless-local-dev
  - aphilosophy

vars:
  primary_tool: Codex CLI
  test_command: ./scripts/run_tests.sh
```

常用 preset：

- `orchestrator`：编排器项目。
- `fullstack`：前后端、部署和 OpenSpec 项目。
- `frontend`：前端主导项目。
- `mobile-sdk`：移动 SDK 或多子工程工作区。

这些 preset 默认包含 `jj-conventions`、`skill-jj-management` 和 `release-conventions`。`release-conventions` 会把 SemVer 版本口径、发布回执边界写入 `AGENTS.md`，并生成 layered `release-notes/README.md`；项目版本条目写入 `.agents/custom/release-notes/README.custom.md` 后再执行 `push --apply`。旧项目的 `modules` 是显式冻结的，升级 CLI 不会自动追加该模块；需要采用发布治理规则时，先把 `release-conventions` 加入现有模块列表，再走 `validate`、dry-run 和 apply。

LLM 接入目标项目时，如果目标项目是 Git 仓库但还没有 `.jj/`，应先确认 `command -v jj && jj --version`，缺失时安装 jj CLI，然后运行 `jj git init --colocate`，再用 `jj status`、`jj log`、`jj bookmark list` 验证。

常用路径：

- `paths.docs_guide_dir`：项目 guide 文档目录，默认 `docs/guides`。
- `paths.spec_dir`：spec 文档目录，默认 `spec`。
- `paths.philosophy_dir`：Agent 哲学决策框架目录，默认 `aphilosophy`。
- `paths.migration_dir`：迁移报告目录，默认 `.agents/migration`。
- `skill_targets.repo_skills`：仓库级 skills 目录，默认 `skills`。
- `skill_targets.codex_project`：新项目默认 `.agents/skills`。已有显式 `.codex/skills` 配置继续支持；未显式配置但 state 已登记旧目录的项目也保留旧目录。迁移方式见本章下方，不能把文件生成当成宿主发现验收。
- `skill_targets.claude_project`：供自定义模块显式引用的保留字段；内置模块不会自动向第三个目录输出。需要 Claude 原生 skills 时，将 `repo_skills` 设置为 `.claude/skills`，同时保持 Codex 的 `codex_project`。根 CLAUDE.md 只是协作入口。

### 已有 Codex 发现目录迁移

1. 在旧配置下运行 `status --project`，先处理被手动修改的托管文件；核对新目录中有无同名非托管文件。
2. 将配置中的 `codex_project` 显式设置为 `.agents/skills`，执行中央与目标 `validate`、`push --dry-run`。
3. `push --apply` 后核对 SKILL.md、支持文件和 `agents/openai.yaml`，尤其是隐式调用策略。
4. 只有新输出完整且旧托管文件无手改时，执行 `push --prune-managed`；非托管文件会保留，冲突时停止并处理。
5. 用宿主技能列表确认发现结果和同名重复项；旧宿主继续使用显式 `.codex/skills` 配置。迁移不创建全局 symlink。
