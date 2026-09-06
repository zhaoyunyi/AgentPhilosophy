# 2026-09-06 审查问题修复与验收

用户已授权按全仓审查建议优化。基线为 `125abbd3`；实现阶段范围包括当前仓库与审查中明确指出的用户级 Superpowers 说明，不同步兄弟项目。2026-09-07 用户进一步授权推进主线、推送和正式发布。

## 行为验收合同

| 项目 | 完成条件 |
| --- | --- |
| 模块来源边界 | 模板、manifest、复制路径、子链接及模板表达式越界被拒绝；失败不写正式文件或冲突候选 |
| 内容指纹 | 系统元数据不产生漂移；实际分发内容变化必然改变指纹；目录链接和显式缓存引用被拒绝 |
| 镜像和打包 | 共用清单、可检查/刷新；清单外残留不进入 wheel；镜像链接不能误删其他文件 |
| 发布身份 | 固定源码 SHA；包内版本、制品摘要与构建回执一致；远端 tag 和下载制品完成独立回读 |
| 技能目录 | 新项目 `.agents/skills`；既有显式/隐式历史目录兼容；迁移保留资源、调用策略及用户文件 |
| Claude 目标 | 文档清楚说明内置两个目标，配置 repo_skills 可输出 Claude 原生技能及完整资源 |
| 跨目录运行 | 独立 Python 目标项目通过 `uv --project` 正确选择中央环境 |
| 规则 | 应急程序不新增权限；文案按受众处理；已授权动作无需重复确认；目录/上下文有缺省行为 |
| Superpowers | 全局说明不再断言已安装；中央参考 6.3.0，保持显式选择，不创建全局发现入口 |
| 上游审查 | 跟踪内容、ref 和正式发布分开输出；单来源错误不漏查其他模块；支持 JSON |
| 文档 | 按任务拆分、索引完整；完整 llm-usage 输出继续可用，缺失或越界 include 明确失败 |
| Skill 更新 | Portless 0.15.6；reverse 精确快照筛选并记录身份/权限差异；Matt/Ponytail 不机械追 ref |

## 上游筛选记录

- Portless 锁定正式 0.15.6、`713f84dec04b5328c02ffc62d1937b27a80fbc5f`，采用脚本端口注入与进程清理边界。安装示例锁定版本，不采用 main 未发布的域名告警。[正式快照](https://github.com/vercel-labs/portless/tree/v0.15.6)
- reverse 选取 v1.0.1 的 `9c28c6ca1062a1a076e28baf40f241dbb4cf5dc2`；其 VERSION 为 1.1.0，标签身份不一致，已在封装中声明。只采用 JSON 路由和证据复核，排除 precedent 预授权、Force 绕过、自动安装与读后副作用要求；没有整体引入上游执行规则。[精确 VERSION](https://github.com/zhaoxuya520/reverse-skill/blob/9c28c6ca1062a1a076e28baf40f241dbb4cf5dc2/VERSION)
- Superpowers 参考 6.3.0、`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`；选择中央模块只分发说明，不安装或启用全局技能。[上游说明](https://github.com/obra/superpowers/blob/v6.3.0/README.md)
- Matt 与 Ponytail 的当前跟踪技能正文无采用新 ref 的必要；code-review-graph、Jinja2、PyYAML 暂无新正式版本需要采用。保留已审阅来源与默认图谱命令兼容性。

## 验证状态

实现与发布验证完成：

- `uv run --locked --offline pytest -q`：222 passed，93.33 秒（2026-09-07 发布前复验）；覆盖新增负向边界、发布模拟、目录兼容、文档组装和实际 wheel 资源清单。
- lint、中央/目标 validate、镜像 check 通过；本仓 dry-run 幂等，status 无漂移警告。
- 仓库 skills 与 Codex 目标共 111 个有效资源文件逐字节一致；旧目录剩余 SKILL.md 为 0，未删除用户自有文件。
- Codex CLI 0.149.1 的原生 `skills/list` 强制回读发现 43 个项目技能，无重复、无解析错误，路径均为 `.agents/skills`。
- 从固定源码快照构建 wheel/sdist；中立目录的安装后 smoke 通过，CLI/content 均为 0.11.0；构建回执绑定源码 SHA 和制品摘要。
- 上游现场回读：Portless/reverse/Superpowers/graph 锁定引用及正式版本匹配；Matt 仅 ref 漂移且跟踪内容未变；Ponytail 的 README 变化被准确报告，未机械更新封装。
- 增加了 [skill 路由验收场景](../agents/skill-routing.md)，没有把元数据/发现检查宣称为付费模型路由评测。

远端验收：[CI 34046345789](https://github.com/zhaoyunyi/AgentPhilosophy/actions/runs/34046345789) 的 macOS/Python 3.12、Linux/Python 3.12/3.14 三组均通过。首轮远端 smoke 暴露 `/var` 与 `/private/var` 路径别名问题，已用最小复现补充回归并统一真实路径。未安装升级 Portless/reverse/Superpowers 的系统工具，也未运行付费模型路由评测。

## 发布收口

`v0.11.0` 已从源码 `aa7cddead2fbfbc51a9be66ea1fffa84b89489b4` 发布，tag、Release、制品摘要和远端 tag 安装均回读通过。主线已包含本轮功能修复及发布回执文档；详情见 [v0.11.0 发布说明](../../release-notes/v0.11.0.md)。
