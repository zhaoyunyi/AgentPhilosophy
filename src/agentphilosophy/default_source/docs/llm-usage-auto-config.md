# AgentPhilosophy 自动配置安装说明（给 LLM）

本文用于“LLM 根据项目具体情况自动选择配置并安装”的场景。只有当用户明确授权你自动判断接入方案时，才使用本模式。

## 一、适用边界

使用本模式时，LLM 负责读取目标项目事实、选择最低有效配置、写入 `.agentphilosophy.yaml`，并执行同步验证。用户不需要逐项选择配置，除非遇到高风险或信息不足的断点条件。

如果用户希望自己选择 preset、模块、路径或可选能力，改用：

```bash
uv run sync.py llm-usage --mode user-breakpoints
```

## 二、执行入口

源码仓库入口：

```bash
uv run sync.py llm-usage --mode auto-config
```

安装版 CLI 入口：

```bash
agentphilosophy-sync llm-usage --mode auto-config
```

## 三、自动判断流程

1. 读取目标项目根目录的 `AGENTS.md`、`CLAUDE.md`、README、`.agentphilosophy.yaml`、`package.json`、workspace 配置、Docker Compose、测试脚本、`spec/`、`docs/`、`skills/`、`.codex/skills/`、`.claude/skills/`。
2. 如果目标项目已经有正式 `.agentphilosophy.yaml`，先加载现有配置，只做增量调整，不重建配置。
3. 如果没有正式 `.agentphilosophy.yaml`，但存在历史 Agent 文档、spec 或 skills，优先执行迁移流程。
4. 如果是全新项目，按项目事实选择 preset 后执行 `init`。
5. 修改配置后必须执行 `validate`、目标项目 `validate`、`push --dry-run`，确认没有 `[error]` 后再 `push --apply`。
6. 最后执行 `status --project`，并汇报最终配置、写入文件和剩余 warning。

## 四、preset 自动选择规则

| 项目事实 | 自动选择 |
| --- | --- |
| 有前后端、API、worker、部署或 OpenSpec 交付链 | `fullstack` |
| 以 Web UI 为主，后端或部署不是当前仓主要边界 | `frontend` |
| iOS、Android、SDK、多子工程或移动端集成仓 | `mobile-sdk` |
| 编排器、任务调度、多 agent workflow 或 provider harness | `orchestrator` |
| 信息不足，无法判断主要边界 | 停止自动写入，返回用户断点 |

## 五、可选模块自动选择规则

LLM 只能选择对当前项目有直接价值的模块，不要为了“更完整”而扩大配置。

| 项目事实 | 自动动作 |
| --- | --- |
| 需要 OpenSpec、proposal、tasks 或 spec-first 交付 | 保留或加入 `openspec-skills` |
| Git 仓库尚未使用 jj，且项目规则要求 jj | 先确认 `jj` 可用，再初始化 colocated jj |
| 目标项目需要 Codex 原生 skill discovery | 保持 `skill_targets.codex_project: .codex/skills` |
| 新项目使用默认 preset | 默认不追加 `superpowers-system`；需要 Superpowers 时由项目显式选择 |
| 项目明确需要统一 Superpowers 固定路径、版本和排障规则 | 追加 `superpowers-system`，再同步刷新 `AGENTS.md` |
| 新项目使用默认 preset | 默认不追加 `skill-ponytail`；需要 Ponytail 时由项目显式选择 |
| 旧项目需要长期复用“能不写就不写、复用优先、避免过度工程”的编码判断 | 追加 `skill-ponytail`，再同步生成 repo skills 和 Codex 项目级 skill |
| 旧项目只是做一次明确的窄范围改动，且用户要求不增加新 skill | 不主动追加 `skill-ponytail` |
| 新项目使用默认 preset，且没有明确要求极简配置 | 保留 `skill-reverse-skill`，同步生成 reverse-skill 授权逆向路由项目级 skill |
| 旧项目需要长期复用授权逆向、安全研究、CTF、APK/JS/二进制/固件分析路由 | 追加 `skill-reverse-skill`，再同步生成 repo skills 和 Codex 项目级 skill |
| 项目没有逆向、安全研究、CTF 或自有资产分析需求，且用户要求极简配置 | 不主动追加 `skill-reverse-skill` |
| 新项目使用默认 preset，且没有明确要求极简配置 | 保留 `skill-improve-codebase-architecture`，同步生成架构评审项目级 skill |
| 旧项目需要长期复用架构评审、重构候选或可测试性改造流程 | 追加 `skill-improve-codebase-architecture`，再同步生成 repo skills 和 Codex 项目级 skill |
| 旧项目只是执行已经明确的局部改动，不需要沉淀架构评审流程 | 不主动追加 `skill-improve-codebase-architecture` |
| 旧项目只需要快速复用 `/code-review`，不需要整条产品工程主线 | 如果未启用 `skill-mattpocock-engineering`，追加 `skill-code-review`，再同步生成 repo skills 和 Codex 项目级 skill |
| 项目已经启用 `skill-mattpocock-engineering` | 不再追加 `skill-code-review`，避免两个模块写入同一个 `code-review` skill 路径 |
| 新项目使用默认 preset，且没有明确要求极简配置 | 保留 `skill-mattpocock-engineering`，同步生成 `/grill-with-docs`、`/to-prd`、`/to-issues`、`/implement`、`/tdd`、`/code-review` 主链路 skill |
| 旧项目需要长期复用“先澄清 -> PRD -> issue -> 单 issue 实现”的产品工程流程 | 追加 `skill-mattpocock-engineering`，再同步生成 repo skills 和 Codex 项目级 skill |
| 旧项目只是一次性明确局部改动，且用户要求极简配置 | 不主动追加 `skill-mattpocock-engineering` |
| 新项目使用默认 preset，且没有明确要求极简配置 | 保留 `skill-portless-local-dev`，同步生成 Portless 本地开发入口判断 skill |
| 只有一次性本地浏览器验收或临时端口冲突 | 不修改 `.agentphilosophy.yaml`，只记录一次性 Portless 使用 |
| 团队需要长期复用 Portless 规则 | 追加 `skill-portless-local-dev`，再同步生成项目级 skill |
| 没有本地 Web/API/移动调试服务 | 不加入 Portless 相关模块 |
| 目标项目要维护或扩展 `aphilosophy` 决策框架 | 追加 `aphilosophy` 和 `skill-philosophy-extraction`，再同步生成哲学脱水项目级 skill |
| 目标项目只是使用已有 `aphilosophy` 文档做决策参考 | 不加入 `skill-philosophy-extraction` |

## 六、必须返回用户断点的情况

遇到以下情况时，不能继续自动安装，必须改用清晰问题让用户选择：

- 需要覆盖或接管已有非托管文件。
- `push --dry-run` 出现 `[error]`。
- warning 影响最终配置边界，例如 module 与 `project_type` 不匹配。
- 项目事实不足以选择 preset。
- 需要启用公网暴露、Tailscale Funnel、修改 `/etc/hosts`、安装 OS service 或触发提权。
- 用户要求保留人工选择权。

断点问题格式参考：

```markdown
## 配置断点：需要确认 preset

我看到这个仓库同时包含 Web UI 和 worker，但没有明确 API 或部署入口。这个选择会决定默认模块和后续托管输出。

推荐选择：`frontend`，因为当前可确认的主体是 Web UI。

可选项：
1. `frontend`：适合前端主导项目，默认输出较轻。
2. `fullstack`：适合后续要纳入 API、worker、部署和 OpenSpec 的项目。
3. 暂不写入配置：我只生成迁移报告，不创建正式 `.agentphilosophy.yaml`。

请回复选项编号或名称，并补充你希望保留的特殊目录或测试命令。
```

## 七、自动模式完成汇报

完成后用中文汇报：

- 选择了哪个 preset，以及依据。
- 新增或保留了哪些 modules，以及依据。
- 是否修改了 `paths`、`skill_targets` 或 `vars.test_command`。
- 执行过哪些验证命令。
- 是否仍有 warning、候选 diff 或需要用户处理的断点。
