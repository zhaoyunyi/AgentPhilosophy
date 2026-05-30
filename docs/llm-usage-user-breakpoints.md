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
```

安装版 CLI 入口：

```bash
agentphilosophy-sync llm-usage --mode user-breakpoints
```

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

当调用方需要机器可解析内容时，在 Markdown 后追加同义 YAML：

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
6. 可选模块：例如 `skill-portless-local-dev` 或 `skill-philosophy-extraction` 是否沉淀为项目级 skill。
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

### 3. Portless 可选模块

```markdown
## 配置断点：是否沉淀 Portless 本地开发规则

我需要确认是否把 Portless 规则写成项目级 skill。这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `skill-portless-local-dev`。

推荐选择：`skip-module`，因为当前只需要一次性本地验收，不需要团队长期复用。

可选项：
1. `skip-module`：不修改项目配置。影响：可以临时使用 Portless，但不会生成项目级 skill。
2. `add-module`：追加 `skill-portless-local-dev`。影响：后续 `push --apply` 会同步 Portless 项目级 skill。
3. `no-portless`：明确不使用 Portless。影响：本地验收继续使用直接端口或现有脚本。

请回复选项编号或 id；如果选择 `add-module`，请说明是否已有团队约定的稳定本地域名。
```

### 4. 哲学脱水可选模块

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

### 5. 验证命令

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

### 6. apply 确认

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
