# AgentPhilosophy CLI 使用说明（给 LLM）

本文只记录当前程序已经实现的 CLI 行为。LLM 执行项目配置任务时，应以本文为准；设计文档中的未来能力不得当成已可用功能。

## 一、运行前提

- 默认在 AgentPhilosophy 仓库根目录运行命令。
- 使用 `uv run sync.py ...` 调用当前源码。
- 如果已经安装 CLI，也可以使用 `agentphilosophy-sync ...`。安装后的 CLI 在当前目录不是中央规范源时，会自动使用包内规范源。
- 命令是否可用以 `uv run sync.py <command> --help` 为准；不要把设计文档里的未来能力当成当前可执行参数。
- 如果从其他目录调用，使用全局参数指定中央源：

```bash
uv run /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy validate
uv run /path/to/AgentPhilosophy/sync.py --source /path/to/AgentPhilosophy push /path/to/project --dry-run
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

## 二、真实可用命令

查看帮助：

```bash
uv run sync.py --help
uv run sync.py init --help
uv run sync.py push --help
uv run sync.py migrate --help
uv run sync.py adopt --help
uv run sync.py status --help
uv run sync.py llm-usage --help
```

校验中央源：

```bash
uv run sync.py validate
```

校验目标项目配置和渲染结果：

```bash
uv run sync.py validate /path/to/project
```

输出给 LLM 使用的当前 CLI 说明：

```bash
uv run sync.py llm-usage
uv run sync.py llm-usage --mode auto-config
uv run sync.py llm-usage --mode user-breakpoints
uv run sync.py llm-usage --mode user-breakpoints --format json
```

`llm-usage` 默认输出完整 CLI 说明，输出格式默认为 Markdown。`--mode auto-config` 输出“LLM 根据项目事实自动选择配置并安装”的精简协议；`--mode user-breakpoints` 输出“LLM 返回用户断点、由用户选择配置后再安装”的精简协议。用户没有明确授权自动选择配置时，优先使用 `user-breakpoints`，并让断点问题包含推荐项、选项影响和回复方式。需要让 agent 直接读取断点标题、推荐项、选项列表和回复格式时，使用 `llm-usage --mode user-breakpoints --format json`。

初始化新项目配置：

```bash
uv run sync.py init /path/to/project --preset mobile-sdk
uv run sync.py init /path/to/project --interactive
```

`init --interactive` 会提示输入 `preset`、`project_name`、`project_type`、`description`、`test_command`，并写入目标项目根目录 `.agentphilosophy.yaml`。它只生成配置，不渲染托管输出，也不自动执行 `push --dry-run` 或 `push --apply`。

安全预览同步计划：

```bash
uv run sync.py push /path/to/project --dry-run
```

应用同步计划：

```bash
uv run sync.py push /path/to/project --apply
```

迁移盘点老项目：

```bash
uv run sync.py migrate /path/to/project
```

当前 `uv run sync.py migrate --help` 已列出 `--write-config`，可执行：

```bash
uv run sync.py migrate /path/to/project --write-config
```

`migrate --write-config` 的边界必须保持严格：先生成 `.agents/migration/proposed.agentphilosophy.yaml` 等迁移草稿；仅当项目根目录 `.agentphilosophy.yaml` 不存在时，才把迁移草稿写入正式配置。若正式配置已存在，必须拒绝覆盖。该参数不接管文件、不写托管输出，也不替代后续 `validate`、`adopt`、`push --dry-run`。

登记接管单个既有文件：

```bash
uv run sync.py adopt /path/to/project --file AGENTS.md --module doc-templates --output agents-md
```

按迁移报告登记接管文件：

```bash
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
```

查看目标项目状态：

```bash
uv run sync.py status --project /path/to/project
```

清理已从当前配置移除且未被手动改动的托管文件：

```bash
uv run sync.py push /path/to/project --prune-managed
```

批量查看或同步 `registry.yaml` 中的项目：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
uv run sync.py push --all --apply
```

批量同步要求 registry 中的目标项目已经存在正式 `.agentphilosophy.yaml`。未接入的项目应先按新项目或老项目迁移流程补齐配置。

批量应用同步成功后，可为本轮确实发生 CLI 版本、内容版本、模块版本或托管输出变化的项目调用大模型更新项目自有文档：

```bash
uv run sync.py push --all --apply \
  --project-name ExampleFullstack \
  --update-docs \
  --llm-command 'codex exec --ephemeral --ignore-user-config --sandbox workspace-write -'
```

每个需要更新文档的 registry 项目必须显式声明项目根目录内的相对路径：

```yaml
projects:
  - name: ExampleFullstack
    path: /absolute/path/to/ExampleFullstack
    documentation_paths:
      - README.md
      - docs
```

`--project-name <名称>` 可重复提供，只处理 registry 中名称完全匹配的项目；未知名称会报错，省略时处理全部登记项目。`--llm-command` 只接受 `codex exec`，并强制要求 `--ephemeral --ignore-user-config --sandbox workspace-write -`；额外可写目录、切换工作根目录、自定义 profile/config、任意输出文件和绕过 sandbox 的参数都会被拒绝。模型任务通过标准输入传入。可用 `--llm-timeout <秒>` 调整每个项目的超时，默认 900 秒。该功能只接受 `--all --apply`：已经完成当前版本文档刷新的项目、同步失败的项目和未声明 `documentation_paths` 的项目不会调用模型。模型完成后 CLI 会复查 state 中登记的全部托管文件、保护文件、版本控制元数据以及文档白名单外的项目文件；任何越界改动都会使当前项目失败，但不会阻断后续 registry 项目。只有成功时才写入包含 `documentation_paths` 的 `documentation_refresh` 指纹，因此模型失败、超时、越界配置、保护漂移或文档范围扩大后可以重试。CLI 不会自动提交、推送或发布文档改动。

`push --prune-managed` 只能针对明确的单个目标项目执行，不能和 `--dry-run`、`--apply` 或 `--all` 混用。它的安全条件是：

- 目标文件必须在 `.agents/agentphilosophy-state.yaml` 中登记过。
- 当前 `.agentphilosophy.yaml` 渲染结果已经不再包含该输出路径。
- 目标文件仍存在时，当前 hash 必须等于 state 里的 `last_written_hash`。
- 文件有手动改动时必须拒绝删除。
- 文件已经缺失时，只清理 state 记录。
- 成功删除文件后，会尝试删除该文件的直接空目录；不会继续向上清理项目父目录。

## 三、版本与更新判断

AgentPhilosophy 使用三层版本判断目标项目是否需要更新：

- CLI 工具版本来自 `pyproject.toml` 和 `agentphilosophy.__version__`，只表示同步程序自身版本。
- 中央规范内容源版本来自 `catalog.yaml` 的 `content_version`，用于判断依赖项目是否需要同步新一轮中央内容。
- 单个模块版本来自各 `module.yaml` 的 `version`，用于判断具体模块是否 stale。
- 外部来源 skill 的上游锁定版本来自各 `module.yaml` 的 `upstream.repository`、`upstream.ref`、`upstream.revision` 和 `upstream.tracked_paths`，用于维护者判断是否需要跟进上游变化。

`agentphilosophy-sync --version` 用于确认当前安装的 CLI release 版本。`push --apply` 和 `adopt` 会把当前 `agentphilosophy_version` 与 `source_content_version` 写入目标项目 `.agents/agentphilosophy-state.yaml`；`status --project` 如果发现 state 中 CLI 版本落后于当前安装包，会输出 `agentphilosophy_version stale: <old> -> <new>`，如果发现内容源版本落后于当前中央源，会输出 `source_content_version stale: <old> -> <new>`。看到 stale 提示时，先运行 `push /path/to/project --dry-run` 审查计划，再决定是否 `--apply`。

如果 state 中的版本高于当前中央源或当前 CLI，`status` 会提示 `source_content_version newer than current source` 或 `agentphilosophy_version newer than current CLI`；此时先检查是否误用了旧的 `--source`、旧安装包或回退后的中央源，不要直接覆盖目标项目。`source_tree_hash` 是源文件指纹，`catalog.yaml` 变更可能同时触发 hash drift 和内容版本提示。

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
  codex_project: .codex/skills
  claude_project: .claude/skills

modules:
  - openspec-skills
  - jj-conventions
  - model-constraints
  - doc-templates
  - multi-module-layout
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
  - skill-ponytail
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

这些 preset 默认包含 `jj-conventions` 和 `skill-jj-management`。LLM 接入目标项目时，如果目标项目是 Git 仓库但还没有 `.jj/`，应先确认 `command -v jj && jj --version`，缺失时安装 jj CLI，然后运行 `jj git init --colocate`，再用 `jj status`、`jj log`、`jj bookmark list` 验证。

常用路径：

- `paths.docs_guide_dir`：项目 guide 文档目录，默认 `docs/guides`。
- `paths.spec_dir`：spec 文档目录，默认 `spec`。
- `paths.philosophy_dir`：Agent 哲学决策框架目录，默认 `aphilosophy`。
- `paths.migration_dir`：迁移报告目录，默认 `.agents/migration`。
- `skill_targets.repo_skills`：仓库级 skills 目录，默认 `skills`。
- `skill_targets.codex_project`：Codex 原生项目级 skill discovery 目录，默认 `.codex/skills`。需要让 Codex 自动发现项目级 skill 时保持该默认值，并在 `push --apply` 后验证 `.codex/skills/**/SKILL.md` 存在。
- `skill_targets.claude_project`：Claude 项目级 skills 目录，默认 `.claude/skills`。

## 五、Superpowers 原生 discovery 版本约束

`superpowers-system` 是显式可选模块，不包含在中央源默认 preset 中。该模块不会复制上游 Superpowers 仓库，也不会生成项目级 `SKILL.md`；它只把 Codex 原生 skill discovery 的固定路径、排障方式和当前项目要求的 Superpowers skill 版本 `6.1.1` 写入 `AGENTS.md`。

目标项目同步后应能在 `AGENTS.md` 看到：

- Superpowers 仓库：`~/.codex/superpowers`
- Skills 入口（symlink）：`~/.agents/skills/superpowers` -> `~/.codex/superpowers/skills`
- 当前项目要求的 Superpowers skill 版本：`6.1.1`

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；已经显式声明 `superpowers-system` 时继续保留，不会因默认值变化自动删除，未声明时升级 CLI 也不会自动追加。需要让旧项目拿到这段约束时，把模块追加到现有 `modules`，不要替换已有模块：

```yaml
modules:
  - existing-module
  - superpowers-system
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
rg -n "Superpowers skill 版本为 `6.1.1`|~/.agents/skills/superpowers" /path/to/project/AGENTS.md
```

## 六、Portless 本地开发入口

Portless 官方仓库：https://github.com/vercel-labs/portless

Portless 用于把本地开发服务从不稳定的端口号改成稳定命名 URL，例如 `https://web.myapp.localhost`。LLM 在目标项目中处理本地启动、浏览器验收、端口冲突、monorepo 多服务、worktree、多端联调或 Tailscale 分享时，应先评估是否需要使用 Portless，但不要把它当成每个项目都必须安装或改造的默认要求。

Portless 接入必须按“最低有效接入深度”选择：

| 项目情况 | 建议动作 |
| --- | --- |
| 没有本地 Web/API/移动调试服务 | 不接入 Portless，只说明不适用原因 |
| 只是本轮 agent 需要稳定 URL 验收 | 优先用已有全局 Portless 或用户已有安装做一次性 `portless run`，不改项目文件 |
| 团队希望稳定复用本地 URL | 作为项目 dev dependency 固定版本，并新增非破坏性脚本，例如 `dev:portless` |
| monorepo / 多 app / 多 worktree | 用根 `portless.json` 或各 package 的 `"portless"` 配置统一命名 |
| Docker Compose、数据库、Mock server 或固定端口服务 | 优先用 `portless alias <name> <port>`，不强行改服务启动脚本 |
| 需要手机、同网段设备或 Tailscale 分享 | 先确认 LAN/Tailscale/Funnel 权限和暴露面，再按需开启，不作为默认路径 |

当前中央源默认 preset 会包含 `skill-portless-local-dev`。该模块会同步生成 `skills/portless-local-dev/SKILL.md` 和 `.codex/skills/portless-local-dev/SKILL.md`，用于让 agent 在本地启动、浏览器验收、端口冲突、多服务、worktree、移动设备联调或 Tailscale 分享任务前先判断是否需要 Portless，以及选择最低有效接入深度。它不会默认安装 Portless、不会默认改项目脚本，也不会把 Portless 当成 QA、线上或 port-forward 入口。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动追加新模块。需要让旧项目长期复用 Portless 判断规则时，把模块追加到现有 `modules`，不要替换已有模块。如果只是一次性本地调试或临时验收，不需要修改 `.agentphilosophy.yaml`。如果目标项目还没有正式 `.agentphilosophy.yaml`，先走新项目 `init` 或老项目 `migrate` 流程。

```yaml
modules:
  - existing-module
  - skill-portless-local-dev
```

加入模块后仍必须走标准同步流程：

```bash
uv run sync.py validate
uv run sync.py validate /path/to/project
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
```

安装版 CLI 的等价入口：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

LLM 进行 Portless 改造时遵循以下顺序：

1. 先读取目标项目 README、`AGENTS.md`、`package.json`、workspace 配置、`turbo.json`、Docker Compose、dev 脚本和测试入口，确认真实本地服务，而不是凭端口习惯猜测。
2. 如果项目没有本地 Web/API/移动调试服务，不要为了 Portless 引入 Node 工具链；记录不适用原因即可。
3. 先判断是否已有可用的全局或项目内 Portless。只有需要团队复用或写入脚本时，才按项目包管理器把 Portless 加为 dev dependency。
4. 安装策略优先遵循项目包管理器。全局安装用 `npm install -g portless`；团队锁版本时作为 dev dependency 安装，例如 `pnpm add -D portless`、`npm install -D portless`、`yarn add -D portless` 或 `bun add -d portless`。
5. Portless 需要 Node.js 24+，且仍是 pre-1.0；项目内安装时应锁版本，并在文档或提交说明中记录升级影响。
6. 不使用一次性远程执行入口，例如 `npx portless`、`pnpm dlx portless`。如果 Portless 已是项目依赖，可以通过 package script 调用本地二进制。
7. 保留直接启动命令作为回退路径，例如 `dev:app`、`dev:raw` 或 `PORTLESS=0 pnpm dev`；不要让 Portless 成为唯一可启动方式。
8. 单应用可从 `portless run <cmd>` 或 `dev:portless` 开始；只有多个 app、worktree 或长期复用时才写 package.json `"portless"` 或根 `portless.json`。
9. Docker 或固定端口服务优先用 `portless alias <name> <port>`；如果服务端口已由 compose、环境变量或平台脚本管理，不要为了 Portless 重写启动拓扑。
10. 多服务代理到另一个 Portless app 时，目标应写稳定 URL，例如 `https://api.myapp.localhost`；Vite、webpack-dev-server 等代理必须设置 `changeOrigin: true`，避免代理循环。
11. 验收必须与接入深度匹配：一次性使用只需证明 URL 可打开和回退可用；项目脚本或配置改造还要证明原直接启动路径仍可用；alias、LAN、Tailscale 要额外验证对应入口。
12. 权限和 CI 边界必须前置：Portless 默认 HTTPS 首跑会生成并信任本地 CA，绑定 443/80 在 macOS/Linux 上可能触发 `sudo`；非交互环境、无 TTY 或 `CI=1` 下不要默认启动需要提示或提权的 Portless，应使用直接端口或预先配置好的代理。
13. 涉及修改 `/etc/hosts`、安装 OS startup service、Tailscale 分享或 Funnel 公网暴露时，先向用户说明影响范围并获得确认；不要把 Funnel 或公网暴露作为默认分享路径。
14. LAN/真机联调使用 `portless proxy start --lan` 时，URL 会切到 mDNS 的 `<name>.local`；该模式会被记住，回到 `.localhost` 前需要显式关闭，例如 `PORTLESS_LAN=0 portless proxy start`。Linux 需要确认 mDNS 工具可用，Next.js 等框架还要按项目配置允许 `.local` dev origin。
15. Tailscale 分享需要先确认 `tailscale` CLI 已安装并连接，Tailscale HTTPS 证书已启用；`--funnel` 还要求 tailnet 和当前节点已启用 Funnel，并会公开暴露服务。
16. 不把 Portless 当作 QA、线上或 port-forward 默认入口。它只解决本地开发、联调、agent 浏览器验收和临时分享。

常见改造片段：

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:portless": "portless run next dev"
  },
  "portless": { "name": "web.myapp" }
}
```

Turborepo 或 workspace 包内脚本：

```json
{
  "scripts": {
    "dev": "portless",
    "dev:app": "next dev"
  },
  "portless": { "name": "web.myapp", "script": "dev:app" }
}
```

根目录 `portless.json`：

```json
{
  "apps": {
    "apps/web": { "name": "web.myapp" },
    "apps/api": { "name": "api.myapp" }
  }
}
```

Docker 或已有固定端口服务：

```bash
portless alias api.myapp 8080
portless alias --remove api.myapp
```

## 七、Ponytail 精简编码 skill

Ponytail 上游仓库：https://github.com/DietrichGebert/ponytail

当前中央源默认 preset 会包含 `skill-ponytail`。该模块会同步生成 `skills/ponytail/SKILL.md` 和 `.codex/skills/ponytail/SKILL.md`，用于让 agent 在新增功能、修 bug、重构或改配置前先判断是否真的需要写代码、能否复用标准库/平台能力/既有依赖，并避免过度工程。

该模块是 AgentPhilosophy 的项目级 skill 封装，不会自动安装上游 Codex 插件或全局 hook。目标项目只要通过 AgentPhilosophy 同步拿到 `skills/ponytail` 和 `.codex/skills/ponytail`，Codex 原生 skill discovery 就能在项目内触发；如果用户明确要求使用上游插件能力，再按上游仓库说明单独安装。

Ponytail 的默认判断顺序：

1. 能不写就不写。
2. 能用语言标准库、框架原生能力、CLI 内置参数或系统工具，就不新增项目代码。
3. 能用项目已有依赖、脚本或 helper，就不新增依赖。
4. 能小改就小改，把变更限制在最接近需求的模块里。
5. 只有重复行为真实出现时才抽象。
6. 只有边界清楚且能隐藏复杂度时才新增模块。

Ponytail 不能用来削减验证、错误处理、安全、可访问性、用户可见流程、BDD/TDD 或项目已有架构边界；它约束的是“少写不必要代码”，不是降低工程标准。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动向旧配置追加新模块。需要让旧项目拿到该 skill 时，把模块追加到现有 `modules`，不要替换已有模块：

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
find -L /path/to/project/.codex/skills/ponytail -name SKILL.md -print
find -L /path/to/project/skills/ponytail -name SKILL.md -print
```

## 八、Reverse Skill 授权逆向路由 skill

reverse-skill 上游仓库：https://github.com/zhaoxuya520/reverse-skill

当前中央源默认 preset 会包含 `skill-reverse-skill`。该模块会同步生成 `skills/reverse-skill/SKILL.md` 和 `.codex/skills/reverse-skill/SKILL.md`，用于让 agent 在 APK/IPA、二进制、前端 JS 签名、固件、恶意样本、PCAP、CTF 或自有资产安全分析前，先确认授权边界、目标类型、用户意图和可用工具链，再路由到合适的方法论。

该模块是 AgentPhilosophy 的项目级 skill 封装，不会自动安装或复制上游完整 `reverse-skill` 仓库，也不会把 IDA、radare2、Frida、jadx、apktool、jshookmcp、anything-analyzer 等工具强制引入目标项目。需要上游完整工具链时，先确认用户已有安装路径或单独 clone 上游仓库，再读取上游 `README_AI.md`、`skills/SKILL.md` 和路由矩阵。

默认使用边界：

1. 只处理授权逆向、安全研究、CTF、测试环境、自有资产或明确授权范围内的材料。
2. 范围不清时先确认目标、权限和允许动作。
3. 不执行凭证窃取、未授权横向移动、持久化、隐蔽投递、反取证或真实环境破坏性利用。
4. 涉及攻击验证时优先给出复现条件、影响判断、检测建议和最小安全 PoC，不扩大到武器化交付。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动向旧配置追加新模块。需要让旧项目拿到该 skill 时，把模块追加到现有 `modules`，不要替换已有模块：

```yaml
modules:
  - existing-module
  - skill-reverse-skill
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
find -L /path/to/project/.codex/skills/reverse-skill -name SKILL.md -print
find -L /path/to/project/skills/reverse-skill -name SKILL.md -print
```

维护中央源时，先用以下命令检查所有带外部来源的 skill 是否有上游更新：

```bash
uv run python scripts/check-skill-upstreams.py
```

如果出现 `[stale] skill-reverse-skill`，先阅读上游 `README.md`、`README_AI.md`、`skills/SKILL.md`、路由矩阵和本轮相关子 skill，再更新 `modules/skill-reverse-skill/templates/SKILL.md.j2`、`module.yaml` 的 `version` / `upstream.revision`、packaged mirror、文档和测试。

## 九、架构加深评审 skill

当前中央源默认 preset 会包含 `skill-improve-codebase-architecture`。该模块会同步生成 `skills/improve-codebase-architecture/SKILL.md` 和 `.codex/skills/improve-codebase-architecture/SKILL.md`，用于让 agent 在用户要求改进架构、寻找重构机会、合并紧耦合模块、提高可测试性或让代码库更容易被 agent 导航时，先做只读架构评审报告。

该 skill 改编自 Matt Pocock 的 `improve-codebase-architecture`（MIT License），但已经按 AgentPhilosophy 的项目愿景收口：

- 先读取项目 `AGENTS.md`、README、`spec/ArchitectureSpec.md`、`spec/DDDSpec.md`、`spec/BDDSpec.md`、`CONTEXT.md` / `CONTEXT-MAP.md` 和 `docs/adr/`。
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
find -L /path/to/project/.codex/skills/improve-codebase-architecture -name SKILL.md -print
find -L /path/to/project/skills/improve-codebase-architecture -name SKILL.md -print
```

## 十、独立 code-review 审查 skill

当前中央源提供可选模块 `skill-code-review`。该模块会同步生成 `skills/code-review/SKILL.md` 和 `.codex/skills/code-review/SKILL.md`，用于让依赖项目快速载入 `/code-review` 双轴审查流程，而不必同步完整 Matt Pocock 产品工程主线。

`skill-code-review` 与 `skill-mattpocock-engineering` 写入同一个 `code-review` skill 路径，不能同时启用。已有项目如果已经启用 `skill-mattpocock-engineering`，说明它已经拥有 `code-review`；只有当项目只需要审查入口、不需要 `/grill-with-docs`、`/to-prd`、`/to-issues`、`/implement` 和 `/tdd` 时，才追加 `skill-code-review`。

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
find -L /path/to/project/.codex/skills/code-review -name SKILL.md -print
find -L /path/to/project/skills/code-review -name SKILL.md -print
```

## 十一、Matt Pocock 产品工程主线 skill

当前中央源默认 preset 会包含 `skill-mattpocock-engineering`。该模块改编自 Matt Pocock 的 `mattpocock/skills`（MIT License），同步生成以下 repo skills 和 Codex 项目级 skills：

- `grill-with-docs`
- `grilling`
- `domain-modeling`
- `to-prd`
- `to-issues`
- `implement`
- `tdd`
- `code-review`

推荐主线：

```text
/grill-with-docs
-> /to-prd
-> /to-issues
-> 新开会话逐个 issue 用 /implement
```

使用含义：

- `/grill-with-docs`：先拷问需求和设计，同时沉淀 `CONTEXT.md`、ADR 和领域语言。
- `/to-prd`：把已经讨论清楚的内容整理成 PRD，不重新访谈。
- `/to-issues`：把 PRD 拆成独立、可验证、适合新会话认领的 vertical slice issue。
- `/implement`：按单个 PRD/issue 实现，内部倾向走 `/tdd`，最后跑 `/code-review`。

更多最佳实践见 [docs/guides/mattpocock-engineering-flow.md](guides/mattpocock-engineering-flow.md)。

已有项目如果是旧版本 `.agentphilosophy.yaml`，模块列表是显式冻结的；升级 CLI 后不会自动向旧配置追加新模块。需要让旧项目拿到该主线时，把模块追加到现有 `modules`，不要替换已有模块：

```yaml
modules:
  - existing-module
  - skill-mattpocock-engineering
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
find -L /path/to/project/.codex/skills -maxdepth 2 -name SKILL.md | sort | rg 'grill-with-docs|to-prd|to-issues|implement|tdd|code-review'
```

## 十二、Agent 哲学决策框架

`aphilosophy` 模块会生成一组触发式参考文档。LLM 不需要在每次任务开始时全量读取它们；只有当任务进入对应冲突或权衡场景时，才按需读取。

- 遇到跨协议冲突、任务妥协、方向选择或连续尝试失败时，读取 `aphilosophy/meta-decision-principles.md`。
- 遇到架构设计、技术选型、抽象层增减、配置化取舍或系统退化判断时，读取 `aphilosophy/architecture-conflict-resolution.md`。
- 遇到多 Agent 协作、角色边界、用户沟通、命名歧义、治理层级或行为校准问题时，读取 `aphilosophy/governance-conflict-resolution.md`。
- 遇到推理前提、方法论失效、递归自省、不确定性分级、错误严重度或能力边界判断时，读取 `aphilosophy/cognitive-conflict-resolution.md`。
- 遇到系统规则、开发者指令、权限边界、服从与自主判断、紧急覆写或失对齐风险时，读取 `aphilosophy/authority-conflict-resolution.md`。

这些文档是通用决策锚点，不覆盖项目自己的 `AGENTS.md`、`spec/` 或 `.agents/custom` 规则。若哲学框架与项目特定规范冲突，以项目特定规范为准；若项目规范前提已经失效，应先向用户说明观察到的事实，再提出可验证的调整建议。

当前中央源还提供可选模块 `skill-philosophy-extraction`。该模块不会默认出现在 preset 中；只有当目标项目需要维护或扩展 `aphilosophy` 决策框架、从哲学/概念性文章中提取可操作规则、生成新的冲突解决协议模板时，才把它加入目标项目 `.agentphilosophy.yaml`。该模块依赖 `aphilosophy`，不能单独启用；加入后，安装版 CLI 会同步生成 `skills/philosophy-extraction/SKILL.md` 和 `.codex/skills/philosophy-extraction/SKILL.md`，让 Codex 原生 skill discovery 能在目标项目内触发。

```yaml
modules:
  - aphilosophy
  - skill-philosophy-extraction
```

启用后仍必须执行标准同步流程：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
```

## 十一、Registry 文件

`registry.yaml` 位于 AgentPhilosophy 中央源根目录，是本机真实批量入口。它可以记录本机绝对路径，且已加入 `.gitignore`，供以下命令读取：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
uv run sync.py push --all --apply
```

`registry.example.yaml` 是可复用模板。新机器或新使用者应复制它为 `registry.yaml`，再把 `path` 改成本机真实路径；不要把 `registry.example.yaml` 当作真实批量同步入口。

需要在批量同步后调用大模型更新项目文档时，为对应项目增加 `documentation_paths`。这些值必须是项目根目录内的相对文件或目录路径；不要写项目根目录、绝对路径、密钥文件、托管文件或代码目录。未声明该字段的项目仍会正常批量同步，但跳过模型阶段。

示例结构：

```yaml
schema_version: 1
projects:
  - name: ExampleProject
    path: /absolute/path/to/ExampleProject
```

## 十二、新项目接入流程

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

## 十三、老项目迁移流程

`migrate` 只做盘点，不会生成正式 `.agentphilosophy.yaml`，也不会覆盖项目已有文件。

```bash
uv run sync.py migrate /path/to/project
```

迁移产物在目标项目的 `.agents/migration/` 下：

- `inventory.md`：既有 Agent、Spec、Skill 文件清单，包括 `skills/`、`.codex/skills/` 和 `.claude/skills/` 下的 `SKILL.md`。
- `proposed.agentphilosophy.yaml`：建议配置草稿。
- `adopt-plan.yaml`：可接管文件清单。
- `diffs/`：候选输出文件。

LLM 必须先检查这些产物。确认配置草稿可用后，再把它作为项目根目录 `.agentphilosophy.yaml`，或使用 `migrate --write-config` 安全写入正式配置。

`migrate --write-config` 只允许在 `.agentphilosophy.yaml` 不存在时从迁移草稿写入正式配置；如果正式配置已存在，必须拒绝覆盖。写入正式配置后，仍然必须继续执行：

```bash
uv run sync.py validate /path/to/project
uv run sync.py adopt /path/to/project --from-report .agents/migration/adopt-plan.yaml
uv run sync.py push /path/to/project --dry-run
uv run sync.py push /path/to/project --apply
```

## 十四、安全边界

- `push` 不带 `--apply` 时不写目标项目文件；`--dry-run` 是推荐显式写法。
- `push --apply` 也不会覆盖未托管的既有文件；遇到冲突会写候选文件到迁移目录。
- `adopt` 不修改目标文件内容，只把当前文件 hash 写入 `.agents/agentphilosophy-state.yaml`。
- `migrate` 只写 `.agents/migration/` 下的报告和候选文件。
- `push --prune-managed` 只清理 state 中登记、当前 hash 仍匹配、且已从当前配置输出中移除的托管文件；文件有手动改动时会拒绝清理。
- `migrate --write-config` 若可用，只能在正式 `.agentphilosophy.yaml` 不存在时写入；存在时必须拒绝覆盖。
- 不要把 `.agents/migration/proposed.agentphilosophy.yaml` 当成正式配置；`push` 只读取项目根目录 `.agentphilosophy.yaml`。
- 修改 `modules` 后必须重新运行 `validate` 和 `push --dry-run`。

## 十五、LLM 执行规则

- 操作前先运行 `uv run sync.py validate`，确认中央源有效。
- 对目标项目写入前必须先运行 `push --dry-run`。
- 在目标项目新增、迁移或沉淀长期有效文档时，必须同时检查主 `AGENTS.md` 或其 layered custom 源是否索引该文档或目录；`docs/` 下的指南、运维记录、问题复盘和部署说明还应更新项目文档索引，例如 `docs/README.md`。若 `AGENTS.md` 是 AgentPhilosophy layered 输出，优先写 `.agents/custom/AGENTS.custom.md` 后再 `push --apply`，不要直接手工改托管结果。
- 读取 `aphilosophy/` 文档应按场景触发，不要把它们当成每次任务的必读上下文。
- 执行可选参数前先看对应 `--help`；帮助里没有的参数不要执行。
- 如果 CLI 输出 `[error]`，停止写入并回报具体错误。
- 如果 CLI 输出 `[warning]`，继续前先判断 warning 是否影响本次目标。
- 不要手工编辑 `.agents/agentphilosophy-state.yaml`。
- 不要把未来设计当成当前能力。
