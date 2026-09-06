---
name: wizard
description: 生成人工可执行的交互式 Bash 向导；适用于基础设施开通、凭据或 CI Secret 配置、第三方控制台操作、一次性迁移或切换，且步骤确实只能由人完成时。
---

# Wizard

改编自 Matt Pocock 的 `wizard` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/wizard

Wizard 把只能由人完成的控制台点击、授权、复制值和不可逆确认，固化为逐阶段交互式 Bash 脚本。Agent 能通过 CLI、API、MCP 或现有权限直接完成的步骤应自行执行，不为它生成向导。

## 流程

1. 先读取 `.env*`、README、compose、框架配置和 `.github/workflows/`，列出全部人工阶段、产生的值、秘密属性和写入位置。
2. 展示阶段顺序，确认哪些值写入 `.env`、GitHub Secret、GitHub Variable 或只用于当前步骤。
3. 对每阶段给出真实 URL、页面路径和取值位置；不确定当前界面时查询一手文档或请用户确认，不编造按钮。
4. 复制 [template.sh](template.sh)，只修改 `STAGES` 标记以下的阶段区；每个阶段只完成一个聚焦任务。
5. 密钥使用隐藏输入；不可逆动作前要求明确确认；写入操作保持幂等。
6. 运行 `bash -n <script>`，可用时运行 `shellcheck <script>`，然后执行 `chmod +x <script>`。不要由 agent 端到端运行需要人工输入或真实凭据的向导。

向导默认是一次性产物，放在 scratch 或临时目录。交付时给出明确运行命令。只有用户要求形成长期可重复入口时才写入 `scripts/`、更新 README，并纳入版本控制。
