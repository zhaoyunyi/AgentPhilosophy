---
name: retro
description: 复盘一次编码会话的 Agent 工作环境；适用于用户输入 /retro、要求会话复盘，或明确要求根据本轮失误改善导航、自动检查、项目指令和工具时。
disable-model-invocation: true
---

# Retro

改编自 Matt Pocock 的 `retro` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/retro

目标：从会话证据提出改善后续 Agent 工作的环境建议。默认只给建议；实施改善需要当前任务已有相应授权。

## 流程

1. 使用 `/writing-for-agents` 的编写原则。读取用户指定会话的一手材料；未指定时使用当前会话。缺少日志时声明证据范围，不把推测写成经历。
2. 检查导航、自动检查、编码规范、项目指令、工具成本、无效规则和信息可达性。先读项目已有 lint/check/test 命令、hooks 和 CI，判断缺少检查还是现有检查未接入或失效。
3. 机械性错误优先落到项目已有 linter、pre-commit 或 CI 的确定性检查；跨文件一致性、领域判断和风格取舍才作为 review 规范。不要用更多指令替代能自动执行的检查。
4. `AGENTS.md` 以必要入口为主，详细规范放在已有文档或 skill，按触发条件导航。删除重复或不改变行为的规则，避免创建第二份真值。
5. 按严重度报告候选：会话证据、影响、推荐改动位置、验证方法和实施范围。没有证据支持的建议标为推测，不自动改全局配置、安装工具或扩大授权。

## 完成条件

- 每个建议可追溯到会话证据或已核实的环境缺口。
- 说明实施者和 reviewer 各自需要的信息；实现过程不机械加载仅 review 需要的规范。
- 已获授权的改善按项目规则实施、验证并更新入口；其余保持建议状态。
