---
name: setup-matt-pocock-skills
description: 为当前仓库配置工程 skills 共用的 issue tracker、triage 标签和领域文档目录；首次使用完整 Matt Pocock 流程前运行一次。
disable-model-invocation: true
---

# Setup Matt Pocock Skills

改编自 Matt Pocock 的 `setup-matt-pocock-skills` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/setup-matt-pocock-skills

这是一次项目设置访谈，不是固定脚本。先查现场，再按章节一次确认一个选择，展示草稿后才写入。

## 目录合同

沿用上游清晰的项目拥有目录：

```text
docs/agents/
├── issue-tracker.md
├── triage-labels.md      # 安装 triage 时才需要
├── domain.md
└── out-of-scope/         # 被明确拒绝的需求知识库
```

本地 issue/spec 继续沿用当前项目已经采用的 `.scratch/<feature>/` 与 `.scratch/<feature>/issues/`。不要创建第二套 `.matt/`、`.skills-config/` 或私有 state 目录。

## 1. 探索

读取 `AGENTS.md`、`CLAUDE.md`、README、`docs/README.md`、`.agentphilosophy.yaml`、`.agents/custom/`、`CONTEXT.md` / `CONTEXT-MAP.md`、`docs/adr/`、`spec/`、`.scratch/` 和版本控制 remote。判断：

- GitHub、GitLab、本地 Markdown、Linear/Jira 或其他 tracker 的现场真值。
- `triage` 是否已安装。
- 单一上下文还是确有多个 bounded context。
- `AGENTS.md` / `CLAUDE.md` 是否是 AgentPhilosophy 托管输出。

## 2. 逐项确认

1. **Issue tracker**：有 GitHub remote 时推荐 GitHub；GitLab remote 推荐 GitLab；无远端或个人项目推荐本地 Markdown；其他 tracker 记录其现有操作合同。
2. **Triage 标签**：安装 `triage` 时推荐保留 `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`；只有现有 tracker 已有词汇时才映射别名。
3. **领域文档**：默认单上下文 `CONTEXT.md + docs/adr/`；只有真实多上下文项目才使用 `CONTEXT-MAP.md` 与上下文内 ADR。

## 3. 展示草稿

展示将写入的 `docs/agents/*.md` 和 Agent 入口索引片段，允许用户修改后再写。

## 4. 写入

- 从本 skill 的 `issue-tracker-*.md`、`triage-labels.md`、`domain.md` 复制并按选择改写。
- 若存在 `.agentphilosophy.yaml`：把入口片段写入 `.agents/custom/AGENTS.custom.md`，不要直接编辑托管的 `AGENTS.md` 或 `CLAUDE.md`；随后执行 `agentphilosophy-sync validate`、目标校验、dry-run、apply。
- 若没有 AgentPhilosophy 配置：优先更新已经存在的 `AGENTS.md` 或 `CLAUDE.md`；两者都不存在时才询问创建哪个。
- `docs/README.md` 存在时加入 `docs/agents/` 入口，避免长期文档无索引。
- 不自动覆盖已有 `docs/agents/*.md`，先合并用户已经维护的合同。

入口片段应只说明 tracker、标签与领域文档在哪里，具体命令留在 `docs/agents/`，避免重复真值。

## 5. 完成

列出写入文件、选择结果和验证命令。说明 `/triage`、`/to-spec`、`/to-tickets`、`/wayfinder`、`/domain-modeling` 将读取这些配置；以后可以直接维护 `docs/agents/*.md`，只有切换 tracker 或目录模型时才需要重跑 setup。
