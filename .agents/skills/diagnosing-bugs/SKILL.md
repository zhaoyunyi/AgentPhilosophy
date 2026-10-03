---
name: diagnosing-bugs
description: 诊断疑难 bug、偶发失败和性能回归；适用于用户要求 diagnose/debug，或问题反复出现但根因不清时。
---

# Diagnosing Bugs

改编自 Matt Pocock 的 `diagnosing-bugs` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/diagnosing-bugs

探索前读取已有 `GLOSSARY.md` 和相关 ADR，使用项目领域语言定位症状与模块。

## 0. 脱敏

本流程会展示命令、输出和采集产物。展示前先把密钥、令牌、Cookie、Authorization、连接串和个人数据替换为 `<REDACTED>`。需要凭据的反馈环通过环境变量读取，不把凭据写进命令、日志、fixture 或聊天内容；HAR、trace 和 dump 只引用承载诊断信号的必要行。

脱敏后证据不足以诊断时，明确说明缺少哪类信号并请求安全的临时观测方式，不要求用户粘贴原始秘密。

## 1. 建立反馈环

先找到一个已经运行过、能够对用户准确症状给出红/绿结果的命令。优先顺序：失败测试、HTTP/CLI 脚本、浏览器脚本、trace 回放、最小 harness、属性循环、版本二分、差分运行。必须尽量快速、确定、聚焦。

无法建立反馈环时，明确列出尝试过的路径，并请求可复现环境、已脱敏的 HAR/日志/core dump/带时间戳录屏或临时观测权限；不要在没有反馈环时直接猜修复。

需要人工点击时，以 [scripts/hitl-loop.template.sh](scripts/hitl-loop.template.sh) 为起点，把步骤和证据固定下来。

## 2. 缩小与假设

反复减小输入、调用链、时间窗口和依赖，保留仍能复现的最小场景。每次只提出一个可证伪假设，写出预期观测，再用日志、断点、指标或实验验证。临时观测统一使用可搜索前缀 `[DEBUG-<topic>]`。

## 3. 定位变化

若存在已知好/坏版本，使用 jj/Git 对应的历史与二分方法；若存在新旧实现或配置，运行相同输入做差分。不要把相关性当根因。

## 4. 修复与回归

在正确 seam 上把最小复现变成失败测试，先看它失败，再实施最小修复并看它通过；随后重跑原始反馈环。没有正确 seam 时，把“架构无法锁定回归”作为发现，并建议用户后续单独运行 `/improve-codebase-architecture`，不要在诊断流程中自动启动仅用户调用的 skill。

## 5. 收尾

- 原始症状不再复现。
- 回归测试通过，或缺失 seam 已记录。
- 删除全部 `[DEBUG-...]` 与临时原型。
- 根因、证据和预防措施写入 change/PR 说明。
