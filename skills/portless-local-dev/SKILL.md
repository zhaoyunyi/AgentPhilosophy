---
name: portless-local-dev
description: 为 AgentPhilosophy 判断、按需安装和改造 Portless 本地开发入口；适用于 localhost 端口冲突、多个本地服务、monorepo/worktree、浏览器验收、移动设备联调、Tailscale 分享或需要稳定 .localhost URL 的任务。
---

# Portless local dev

Portless 官方仓库：https://github.com/vercel-labs/portless

## 何时使用

在以下场景优先评估 Portless，但不要默认安装或改造项目：

- 项目有 Web、API、docs、admin、storybook、Expo、React Native 或其他本地 dev server。
- 多个服务需要同时启动，端口容易冲突或被 agent 猜错。
- Browser/Playwright/e2e 验收需要稳定 URL，而不是随机或记忆中的 `localhost:3000`。
- monorepo、Turborepo、pnpm workspace、git worktree 需要给不同 app 或不同工作区稳定命名。
- OAuth callback、CORS、cookie、localStorage、Tailscale 分享或真实移动设备联调依赖稳定 origin。

如果仓库没有本地 Web/API/移动调试服务，不要为了使用 Portless 引入 Node 工具链；只在用户明确要求时记录“不适用”和原因。

## 接入深度决策

先按项目具体情况选择最低有效接入深度：

| 项目情况 | 推荐做法 |
| --- | --- |
| 没有本地 Web/API/移动调试服务 | 不接入，只说明 Portless 不适用 |
| 只是当前任务需要浏览器验收 | 使用已有全局或项目内 Portless 做一次性 `portless run`，不改文件 |
| 团队要稳定复用 URL | 加 dev dependency，新增 `dev:portless` 或等价非破坏性脚本 |
| monorepo、多 app、多 worktree | 用根 `portless.json` 或各 package `"portless"` 命名 |
| Docker Compose、数据库、mock server、固定端口服务 | 用 `portless alias <name> <port>`，不要重写服务拓扑 |
| 手机、同网段设备、Tailscale 分享 | 先确认权限、网络和暴露面，再开启 LAN/Tailscale/Funnel |

不要把 Portless 改造成唯一启动方式。保留原命令，并让用户能用 `PORTLESS=0` 或 `dev:raw` 回退。

## 先判断项目现状

1. 读取根目录和相关子目录的 `AGENTS.md`、README、`package.json`、workspace 配置、`turbo.json`、Docker Compose、dev 脚本和测试入口。
2. 确认包管理器：优先遵循已有 lockfile 和脚本，不混用 npm/pnpm/yarn/bun。
3. 找出真实启动命令、服务边界和期望主机名；主机名必须由项目名、包名或目录名转成小写 ASCII slug，例如 `web.myapp.localhost`、`api.myapp.localhost`，不要直接使用包含空格、中文或特殊字符的展示名。
4. 判断框架是否读取 `PORT` 环境变量；Portless 会自动处理常见框架，但自定义 server 仍应显式读取 `process.env.PORT`。
5. 判断是否已有全局 `portless` 或项目内依赖；只有需要团队复用、写脚本或锁版本时才修改 package 文件。
6. 写改造前先保留一个无 Portless 的直接启动路径，便于 `PORTLESS=0`、`pnpm run dev:app` 或 `pnpm run dev:raw` 回退。

## 安装策略

- 全局安装适合个人机器和多项目协作：`npm install -g portless`。
- 项目内安装适合团队锁版本：使用项目包管理器添加 dev dependency，例如 `npm install -D portless`、`pnpm add -D portless`、`yarn add -D portless` 或 `bun add -d portless`。
- Portless 需要 Node.js 24+，且仍是 pre-1.0；项目内安装时应锁版本并记录升级影响。
- 不使用一次性的 `npx portless`、`pnpm dlx portless` 或类似远程临时执行方式；如果是项目依赖里的本地二进制，可通过 package script 调用。

## 改造模式

单应用项目可先做非破坏性脚本：

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:portless": "portless run next dev"
  },
  "portless": { "name": "myapp" }
}
```

如果只是当前任务需要稳定 URL，优先保留项目文件不变，让 agent 和验收命令显式运行：

```bash
portless
portless run --name myapp pnpm dev
```

Turborepo 或 workspace 在需要长期复用时再写入 package 配置：

```json
{
  "scripts": {
    "dev": "portless",
    "dev:app": "next dev"
  },
  "portless": { "name": "web.myapp", "script": "dev:app" }
}
```

多 app 或多 worktree 场景可在根目录放 `portless.json` 统一命名：

```json
{
  "apps": {
    "apps/web": { "name": "web.myapp" },
    "apps/api": { "name": "api.myapp" }
  }
}
```

Docker、数据库、mock server 或其他固定端口服务优先使用 alias：

```bash
portless alias api.myapp 8080
portless alias --remove api.myapp
```

多服务代理：

- 前端代理到另一个 Portless app 时，目标写稳定 URL，例如 `https://api.myapp.localhost`。
- Vite、webpack-dev-server 等代理必须设置 `changeOrigin: true`，否则可能触发代理循环。
- 单独运行在 Portless 外部的 Node 进程访问 HTTPS Portless app 时，按需要配置 `NODE_EXTRA_CA_CERTS=~/.portless/ca.pem`，或在本地调试中改用 `--no-tls`。

## 常用命令

```bash
portless --version
portless trust
portless list
portless get myapp
portless prune
portless hosts sync
portless proxy start
portless proxy start --no-tls
portless proxy start --lan
portless proxy start --tld localhost --tld test
PORTLESS_TLD=localhost,test portless proxy start
PORTLESS_LAN=0 portless proxy start
portless myapp --tailscale pnpm dev
portless myapp --funnel pnpm dev
portless service install
PORTLESS=0 pnpm dev
```

## LAN 和真机联调

- `portless proxy start --lan` 会使用 mDNS，把服务暴露为 `<name>.local`，适合手机或同网段设备访问。
- LAN 模式会被 Portless 记住；如果要回到 `.localhost`，显式运行 `PORTLESS_LAN=0 portless proxy start` 或按当前项目脚本关闭 LAN 模式。
- macOS 自带 `dns-sd`；Linux 需要确认 `avahi-utils` 或等价 mDNS 工具可用。
- Next.js 使用 `.local` hostname 时，需要在 `next.config.js` 的 `allowedDevOrigins` 中加入对应域名，例如 `myapp.local` 和 `*.myapp.local`。

## Tailscale 和 Funnel

- Tailscale 分享前先确认 `tailscale` CLI 已安装并 `tailscale status` 可用。
- `--tailscale` 需要 Tailscale HTTPS 证书已启用；`portless list` 应能看到本地 URL 和 tailnet URL。
- `--funnel` 会公开暴露服务，还要求 tailnet 和当前节点都启用 Funnel；不要把它作为默认分享路径。
- 可以用 `PORTLESS_TAILSCALE=1` 或 `PORTLESS_FUNNEL=1` 设置默认行为，但只有在用户明确确认分享范围后才能写入项目或 shell 配置。

## 验收标准

- 能从 `portless list` 看到期望服务名和 URL。
- 浏览器或 Browser/Playwright 能打开稳定 URL，例如 `https://web.myapp.localhost`；一次性使用不要求写入项目配置。
- 原直接启动命令仍可作为回退路径，或 `PORTLESS=0 <原命令>` 可用。
- 项目脚本或 `portless.json` 改造后，必须证明原脚本、Portless 脚本和回退路径都可用。
- 多服务场景中，前端、API、WebSocket、OAuth callback、CORS 和 cookie origin 都指向稳定 hostname。
- worktree 场景中不同工作区不会互相抢端口；必要时检查生成的子域名前缀。
- Safari 或系统 DNS 无法解析 `.localhost` 子域名时，运行 `portless hosts sync` 并记录清理方式 `portless hosts clean`。
- 如果需要同一组 app 同时支持多个本地域名后缀，可重复传 `--tld`，或用逗号分隔的 `PORTLESS_TLD`；记录主 URL 仍以第一个 TLD 为准。

## 安全边界

- 不在 CI 中默认启动需要交互或提权的 Portless；CI 应使用直接端口或预先配置好的代理。
- 默认 HTTPS 首跑会生成并信任本地 CA；绑定 443/80 在 macOS/Linux 上可能触发 `sudo`；非交互环境、无 TTY 或 `CI=1` 下 Portless 会直接失败而不是提示。
- 不把 Portless 当线上入口或 QA 默认入口；它只解决本地开发、联调和分享。
- 涉及 sudo、信任本地 CA、`/etc/hosts`、OS startup service、Tailscale Funnel 时，先说明影响范围，并给出 `portless clean` 或对应卸载命令。
