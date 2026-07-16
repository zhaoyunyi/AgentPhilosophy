# AgentPhilosophy 用户断点配置说明（给 LLM）

本文用于“LLM 返回用户断点，让用户选择配置后再安装”的场景。目标是让用户看得懂每个选择会改变什么，并能安全地决定最终 `.agentphilosophy.yaml`。

## 一、适用边界

使用本模式时，LLM 不直接替用户决定关键配置。LLM 先读取项目事实，再在需要选择的位置暂停，返回结构清晰的问题。用户回复后，LLM 根据选择修改配置并执行安装流程。

如果用户已经授权 LLM 自动选择配置，改用：

```bash
uv run sync.py llm-usage --mode auto-config
```

## 二、执行入口

源码仓库入口：

```bash
uv run sync.py llm-usage --mode user-breakpoints
uv run sync.py llm-usage --mode user-breakpoints --format json
```

安装版 CLI 入口：

```bash
agentphilosophy-sync llm-usage --mode user-breakpoints
agentphilosophy-sync llm-usage --mode user-breakpoints --format json
```

不传 `--format` 时默认输出 Markdown；`--format json` 输出机器可解析结构，供 agent 直接读取断点标题、推荐项、选项列表和 `reply_format`。

## 三、断点问题标准格式

每个断点必须只问一个配置主题，避免把多个选择混在一起。问题必须包含“为什么要选”、“推荐项”、“每个选项的影响”和“用户回复方式”。

```markdown
## 配置断点：<配置主题>

我需要你确认 <配置项>，因为 <这个选择会影响哪些文件、模块或后续同步行为>。

推荐选择：`<选项 id>`，因为 <基于项目事实的简短理由>。

可选项：
1. `<选项 id>`：<适用场景>。影响：<会写入或不会写入什么>。
2. `<选项 id>`：<适用场景>。影响：<会写入或不会写入什么>。
3. `<选项 id>`：<适用场景>。影响：<会写入或不会写入什么>。

请回复选项编号或选项 id；如果要覆盖默认值，请同时给出具体值。
```

当调用方需要机器可解析内容时，使用 `--format json`。JSON 结构与 Markdown 模板同义，完整数据由 CLI 输出：

```json
{
  "mode": "user-breakpoints",
  "format_version": 1,
  "breakpoints": [
    {
      "id": "preset-selection",
      "title": "选择 preset",
      "recommended": {
        "id": "fullstack",
        "reason": "项目包含 Web、API、worker、部署或 OpenSpec 入口时默认选择更完整。"
      },
      "options": [
        {
          "id": "fullstack",
          "label": "前后端、API、worker、部署或 OpenSpec 项目",
          "impact": "写入 fullstack preset 默认 modules。"
        },
        {
          "id": "frontend",
          "label": "前端主导项目",
          "impact": "写入 frontend preset 默认 modules。"
        }
      ],
      "reply_format": "回复选项编号或 id"
    }
  ]
}
```

Markdown 中仍可追加同义 YAML，便于不调用 JSON 入口的 agent 读取：

```yaml
breakpoint:
  id: preset-selection
  question: 请选择目标项目 preset
  recommended: fullstack
  options:
    - id: fullstack
      label: 前后端或部署项目
      impact: 写入 fullstack preset 默认 modules
    - id: frontend
      label: 前端主导项目
      impact: 写入 frontend preset 默认 modules
  reply_format: 回复选项编号或 id
```

## 四、推荐断点顺序

按以下顺序提问。每次只提出当前必须解决的断点；用户回答后再进入下一步。

1. 项目接入路径：新项目 `init`、老项目 `migrate`、或已有配置增量调整。
2. preset：`fullstack`、`frontend`、`mobile-sdk`、`orchestrator` 或暂不写入。
3. 项目基础信息：`project_name`、`project_type`、`description`。
4. 目录路径：`paths.docs_guide_dir`、`paths.spec_dir`、`paths.philosophy_dir`。
5. skill 输出位置：`skill_targets.repo_skills`、`skill_targets.codex_project`、`skill_targets.claude_project`。
6. 可选模块：例如 `skill-ponytail`、`skill-reverse-skill`、`skill-improve-codebase-architecture`、`skill-code-review`、`skill-mattpocock-engineering`、`skill-portless-local-dev` 或 `skill-philosophy-extraction` 是否沉淀为项目级 skill。
7. 验证命令：`vars.test_command`。
8. 老文件接管：是否按 `adopt-plan.yaml` 接管已有文件。
9. dry-run 结果确认：是否允许执行 `push --apply`。

## 五、常用断点模板

### 1. 接入路径

```markdown
## 配置断点：选择接入路径

我需要确认这个项目是新接入还是迁移接管。这个选择会决定是否直接创建 `.agentphilosophy.yaml`，以及是否先生成 `.agents/migration/` 报告。

推荐选择：`migrate`，因为仓库里已经有 AGENTS、spec 或 skills 内容。

可选项：
1. `migrate`：适合已有 Agent 文档或 skills 的项目。影响：先生成迁移报告和候选配置，不覆盖正式配置。
2. `init`：适合全新项目。影响：直接创建 `.agentphilosophy.yaml`。
3. `adjust-existing`：适合已经有 `.agentphilosophy.yaml` 的项目。影响：只做增量修改。

请回复选项编号或 id。
```

### 2. preset

```markdown
## 配置断点：选择 preset

我需要确认项目 preset。preset 会决定默认 modules、jj 规则、文档模板和后续托管输出。

推荐选择：`fullstack`，因为我看到了 Web、API 或部署相关入口。

可选项：
1. `fullstack`：适合前后端、API、worker、部署或 OpenSpec 项目。影响：默认配置更完整。
2. `frontend`：适合前端主导项目。影响：默认配置更轻。
3. `mobile-sdk`：适合 iOS、Android、SDK 或多子工程移动仓。影响：默认测试规则偏移动端。
4. `orchestrator`：适合任务编排、多 agent workflow 或 provider harness。影响：默认关注编排协作边界。

请回复选项编号或 id。
```

### 3. Superpowers 原生 discovery 版本约束

```markdown
## 配置断点：是否同步 Superpowers 6.1.1 约束

我需要确认是否把 Superpowers 的 Codex 原生 discovery 固定路径、版本和排障规则写入 `AGENTS.md`。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `superpowers-system`。

推荐选择：`skip-module`，因为 Superpowers 是项目可选能力；只有项目明确需要统一其安装位置、版本和排障方式时才追加。

可选项：
1. `skip-module`：不修改项目配置。影响：保持默认 preset，不新增 Superpowers 约束。
2. `add-module`：追加 `superpowers-system`。影响：后续 `push --apply` 会刷新 `AGENTS.md` 中的 Superpowers 6.1.1 约束。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。

请回复选项编号或 id。
```

### 4. Ponytail 精简编码 skill

```markdown
## 配置断点：是否安装 Ponytail 精简编码 skill

我需要确认是否把 Ponytail 的“能不写就不写、复用优先、避免过度工程”规则写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-ponytail`。

推荐选择：`skip-module`，因为 Ponytail 是项目可选能力；只有项目明确需要长期复用精简编码判断时才追加。

可选项：
1. `skip-module`：保持默认配置。影响：不新增 Ponytail skill。
2. `add-module`：追加 `skill-ponytail`。影响：后续 `push --apply` 会同步 repo skills 和 Codex 项目级 skill。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。

请回复选项编号或 id。
```

### 5. reverse-skill 授权逆向路由 skill

```markdown
## 配置断点：是否安装 reverse-skill 授权逆向路由 skill

我需要确认是否把 reverse-skill 的授权逆向、安全研究、CTF 和本机工具链路由写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-reverse-skill`。

推荐选择：`add-module`，因为默认 preset 会把它作为通用 skill 集合的一部分，便于后续 APK/JS/二进制/固件/CTF 或自有资产安全分析任务先确认授权边界并正确分流。

可选项：
1. `add-module`：追加 `skill-reverse-skill`。影响：后续 `push --apply` 会同步 repo skills 和 Codex 项目级 skill。
2. `skip-module`：不修改旧项目配置。影响：本次升级不会新增 reverse-skill 路由 skill。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。

请回复选项编号或 id。
```

### 6. 架构加深评审 skill

```markdown
## 配置断点：是否安装架构加深评审 skill

我需要确认是否把架构评审和重构候选流程写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-improve-codebase-architecture`。

推荐选择：`add-module`，因为默认 preset 会把它作为通用 skill 集合的一部分，便于后续做架构评审和可测试性改造。

可选项：
1. `add-module`：追加 `skill-improve-codebase-architecture`。影响：后续 `push --apply` 会同步 repo skills 和 Codex 项目级 skill。
2. `skip-module`：不修改旧项目配置。影响：本次升级不会新增架构评审 skill。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。

请回复选项编号或 id。
```

### 7. 独立 code-review 审查 skill

```markdown
## 配置断点：是否安装独立 code-review 审查 skill

我需要确认是否只把 `/code-review` 双轴审查流程写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-code-review`。

推荐选择：`add-module`，因为当前只需要快速载入审查入口，不需要同步 `/grill-me`、`/grill-with-docs`、`/to-spec`、`/to-tickets`、`/implement` 和 `/tdd` 整条产品工程主线。

可选项：
1. `add-module`：追加 `skill-code-review`。影响：后续 `push --apply` 会同步 `code-review` 的 repo skill 和 Codex 项目级 skill。
2. `use-mattpocock`：改用或保留 `skill-mattpocock-engineering`。影响：同时同步 Matt Pocock 产品工程主线和 `code-review`，不要再追加 `skill-code-review`。
3. `skip-module`：不修改旧项目配置。影响：本次升级不会新增独立 code-review skill。

请回复选项编号或 id。
```

### 8. Matt Pocock 产品工程主线 skill

```markdown
## 配置断点：是否安装 Matt Pocock 产品工程主线 skill

我需要确认是否把 Matt Pocock 的 `/grill-with-docs -> /to-spec -> /to-tickets -> /implement` 主线写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-mattpocock-engineering`。

推荐选择：`add-module`，因为默认 preset 会把它作为通用 skill 集合的一部分，便于后续先澄清需求，再沉淀 spec、拆 ticket，并逐个 ticket 新开会话实现。

可选项：
1. `add-module`：追加 `skill-mattpocock-engineering`。影响：后续 `push --apply` 会同步 `grill-me`、`grill-with-docs`、`to-spec`、`to-tickets`、兼容入口 `to-prd`、`to-issues`、`implement`、`tdd`、`code-review` 等 repo skills 和 Codex 项目级 skill。
2. `skip-module`：不修改旧项目配置。影响：本次升级不会新增 Matt Pocock 产品工程主线 skill。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。

请回复选项编号或 id。
```

### 9. Portless 本地开发判断 skill

```markdown
## 配置断点：旧项目是否补上 Portless 本地开发判断 skill

我需要确认是否把 Portless 判断规则写成项目级 skill。新项目默认 preset 已包含该模块；旧项目的模块列表是显式冻结的，这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-portless-local-dev`。

推荐选择：`skip-module`，因为当前只需要一次性本地验收，不需要团队长期复用。

可选项：
1. `skip-module`：不修改项目配置。影响：可以临时使用 Portless，但不会生成项目级 skill。
2. `add-module`：追加 `skill-portless-local-dev`。影响：后续 `push --apply` 会同步 Portless 项目级 skill。
3. `no-portless`：明确不使用 Portless。影响：本地验收继续使用直接端口或现有脚本。

请回复选项编号或 id；如果选择 `add-module`，请说明是否已有团队约定的稳定本地域名。
```

### 10. 哲学脱水可选模块

```markdown
## 配置断点：是否安装哲学脱水 skill

我需要确认是否把哲学/概念性文章脱水规则写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-philosophy-extraction`。

推荐选择：`skip-module`，因为当前只是使用已有 `aphilosophy` 决策文档，不需要扩展模板。

可选项：
1. `skip-module`：不修改项目配置。影响：继续使用已有 `aphilosophy` 文档，不生成额外 skill。
2. `add-module`：追加 `aphilosophy` 和 `skill-philosophy-extraction`。影响：后续 `push --apply` 会同步哲学决策文档、repo skills 和 Codex 项目级 skill。
3. `no-aphilosophy-extension`：明确不在本项目维护哲学提取流程。影响：只保留项目当前 Agent 规则。

请回复选项编号或 id；`add-module` 会同时启用 `aphilosophy`，因为哲学脱水 skill 依赖这组决策文档。
```

### 11. 验证命令

```markdown
## 配置断点：确认测试命令

我需要确认 `vars.test_command`，因为生成的规范会要求完成前运行这个命令。

推荐选择：`existing-script`，因为项目 README 或 package 脚本里已有测试入口。

可选项：
1. `existing-script`：使用我识别到的命令 `<命令>`。影响：写入 `vars.test_command`。
2. `custom`：你提供一个命令。影响：按你的回复写入 `vars.test_command`。
3. `empty`：暂不写测试命令。影响：保留为空，后续规范只使用默认提示。

请回复选项编号或 id；如果选择 `custom`，请直接给出命令。
```

### 12. apply 确认

```markdown
## 配置断点：是否应用 dry-run 计划

`push --dry-run` 已完成，我需要你确认是否写入目标项目。这个选择会决定是否创建或更新托管输出和 `.agents/agentphilosophy-state.yaml`。

推荐选择：`apply`，因为 dry-run 没有 error，且候选写入符合刚才确认的配置。

可选项：
1. `apply`：执行 `push --apply`。影响：写入托管输出和 state。
2. `review-diff`：先查看候选 diff。影响：暂不写入正式输出。
3. `stop`：停止安装。影响：保留当前文件，不执行 apply。

请回复选项编号或 id。
```

## 六、用户回复后的安装流程

用户回复后，LLM 必须：

1. 复述最终选择，避免误解。
2. 修改或创建 `.agentphilosophy.yaml`。
3. 执行 `uv run sync.py validate`。
4. 执行 `uv run sync.py validate /path/to/project`。
5. 执行 `uv run sync.py push /path/to/project --dry-run`。
6. 如用户已确认 apply，执行 `uv run sync.py push /path/to/project --apply`。
7. 执行 `uv run sync.py status --project /path/to/project`。
8. 用中文汇报写入内容、验证结果和剩余风险。
