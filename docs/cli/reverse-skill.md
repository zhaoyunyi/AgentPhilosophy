## 八、Reverse Skill 授权逆向路由 skill

reverse-skill 上游仓库：https://github.com/zhaoxuya520/reverse-skill

当前中央源默认 preset 会包含 `skill-reverse-skill`。该模块已对齐上游 `v1.0.1` 正式版和当前主线扩展路由面，会把 `SKILL.md`、`agents/openai.yaml` 与 MIT 许可证同时生成到 `skills/reverse-skill/` 和 `.agents/skills/reverse-skill/`。agent 在 APK/IPA、二进制、前端 JS 签名、协议、取证、云/K8s、代码审计、硬件等安全任务前，先建立 `auth`、in/out-of-scope 和 `network_profile`，授权未 granted 时不 ACT，再按 `MASTER-ROUTING` 方法选择 PRIMARY，并用 `Evidence -> Finding -> Path` 保留证据链。

该模块是 AgentPhilosophy 的项目级 skill 封装，不会自动安装或复制上游完整 `reverse-skill` 仓库，也不会把 IDA、radare2、Frida、jadx、apktool、jshookmcp、anything-analyzer 等工具强制引入目标项目。需要上游完整工具链时，先确认用户已有安装路径或单独 clone 上游仓库，再读取上游 `README_AI.md`、`skills/SKILL.md`、`skills/MASTER-ROUTING.md`、`skills/ops/` 和路由矩阵。AgentPhilosophy 不继承任何以 precedent 或其他措辞解除安全审查的上游指令。

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
find -L /path/to/project/.agents/skills/reverse-skill -name SKILL.md -print
find -L /path/to/project/skills/reverse-skill -name SKILL.md -print
```

维护中央源时，先用以下命令检查所有带外部来源的 skill 是否有上游更新：

```bash
uv run python scripts/check-skill-upstreams.py
```

如果出现 `[stale] skill-reverse-skill`，先阅读上游 `README.md`、`README_AI.md`、`skills/SKILL.md`、路由矩阵和本轮相关子 skill，再更新 `modules/skill-reverse-skill/templates/SKILL.md.j2`、`module.yaml` 的 `version` / `upstream.revision`、packaged mirror、文档和测试。

## 本地筛选边界

当前封装选择正式标签 v1.0.1 的提交 `9c28c6ca1062a1a076e28baf40f241dbb4cf5dc2`。该快照 VERSION 写为 1.1.0，与标签不一致，来源以提交识别。路由以 routing.json 为准；不采用 precedent 预授权、Force 绕过、读后副作用或自动安装要求。详情以中央 skill 和本轮[筛选记录](../plans/2026-09-06-audit-remediation.md)为准。
