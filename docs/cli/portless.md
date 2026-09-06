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

当前中央源默认 preset 会包含 `skill-portless-local-dev`。该模块已对齐 Portless `0.15.6`，会把 `SKILL.md`、`agents/openai.yaml` 和 Apache-2.0 许可证同时生成到 `skills/portless-local-dev/` 与 `.agents/skills/portless-local-dev/`，用于让 agent 在本地启动、浏览器验收、端口冲突、多服务、worktree、移动设备联调或 Tailscale 分享任务前先判断是否需要 Portless，以及选择最低有效接入深度。排障优先运行只读 `portless doctor`；非 LAN 模式只监听 `127.0.0.1` 与 `::1`，显式 LAN 模式才监听所有网卡。它不会默认安装 Portless、不会默认改项目脚本，也不会把 Portless 当成 QA、线上或 port-forward 入口。

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
