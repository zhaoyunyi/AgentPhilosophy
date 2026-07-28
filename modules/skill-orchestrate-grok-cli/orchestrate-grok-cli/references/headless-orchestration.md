# Grok CLI headless 编排手册

## 1. 现场预检

先确认实际二进制和当前版本支持的参数，不凭旧命令猜测：

```bash
command -v grok
grok --version
grok --help
grok agent headless --help
grok inspect
```

用户把 `grok` 写成 `gork` 时，先用 `command -v` 判断是否存在同名包装器；没有时按用户语义使用 `grok`，不要静默安装另一个程序。

当前 CLI 有两类不同入口：

- `grok --prompt-file <path>`、`grok --prompt-json <json>` 或 `grok -p <prompt>`：单次 headless 任务，完成后退出。
- `grok agent headless`：启动 Grok WebSocket relay，供 SDK 或 WebSocket 客户端连接；它不接收任务 prompt。

## 2. 建立可审计基线

每轮编排先记录：

- 绝对 cwd、仓库类型和项目指令；
- 当前工作区状态、基线 revision、用户已有 WIP；
- 本任务允许写入的文件和明确禁止修改的文件；
- 验证命令、用户可见验收点以及是否允许提交、推送、发布或外部写入。

默认只授权本地任务所需的修改和验证。没有明确授权时，prompt 必须写明：不读取密钥、不操作生产、不提交、不推送、不发布。

## 3. 拆分并行任务

只有同时满足以下条件才并行：

1. 子任务目标和验收标准独立；
2. 写入目录或文件不重叠；
3. 每个执行者有独立工作区，或共享工作区中只有一个写入者；
4. 失败不会让另一个任务的基线失效。

为每个执行者准备单独 prompt 文件。建议结构：

```text
目标：一句话说明交付结果。
工作目录：绝对路径。
先读：项目指令和必要上下文路径。
只允许修改：精确文件或目录列表。
禁止：未授权路径、凭据、生产、提交、推送、发布。
验收：可观察行为和必须运行的验证命令。
交付：列出实际修改、验证结果、遗留风险；不要声称未执行的验证。
```

## 4. 配置 Stop 结束信号

Grok 原生扫描全局 `~/.grok/hooks/*.json` 和项目 `<repo>/.grok/hooks/*.json`。全局 hook 能覆盖多个隔离工作区，适合并行编排；项目 hook 只适合单仓任务，并且需要 folder trust。hook 在新会话启动时加载。

优先使用 skill 自带脚本，以显式绝对路径创建独立配置、handler 和 JSONL 日志：

```bash
bash scripts/grok-stop-hook.sh install \
  --hooks-dir /absolute/grok-home/hooks \
  --runtime-dir /absolute/runtime \
  --name member-61
grok inspect | sed -n '/Hooks/,/Config Sources/p'
```

安装前后对比 `grok inspect` 的 Hooks 计数；只有新增的 command hook 确实出现后才能把它纳入结束判定。项目 hook 未出现时先修复 trust，或切换到全局 hooks 目录，不要直接启动任务。

handler 只记录 `hook_event_name`、`session_id`、`cwd`、`reason` 和时间戳，不记录 prompt 或 tool payload。若使用全局 hook，同一时段其他 Grok 会话也会触发它；必须按本轮 cwd、session ID 与启动时间过滤。

Stop 事件只表示 agent 在一次真正完成处准备结束，不表示修改正确，也不替代进程退出码。用户中断不会产生正常 Stop；API 失败可能产生 `StopFailure` 或进程错误。

## 5. 启动一次性 headless 任务

典型无人值守命令：

```bash
grok \
  --cwd /absolute/workspace \
  --prompt-file /absolute/prompts/member-61.md \
  --always-approve \
  --permission-mode bypassPermissions \
  --no-plan \
  --output-format streaming-json \
  --max-turns 40
```

`--always-approve` 与 `bypassPermissions` 表示 Grok 工具调用无需等待交互确认，但 deny 规则和 hooks 仍可阻断。自动批准不是权限来源；用 `--deny`、`--disallowed-tools`、隔离工作区和明确 prompt 缩小能力面。

只读审查可移除写工具，例如：

```bash
grok -p "审查当前改动并列出问题，不修改文件" \
  --disallowed-tools "search_replace" \
  --output-format json
```

## 6. 轮询与结束判定

每个执行进程单独保存：启动时间、cwd、prompt 路径、PID 或运行句柄、输出日志和预期 hook 名称。轮询时读取增量输出，不重复灌入完整日志。

`streaming-json` 是 JSONL，事件类型至少包括 `text`、`thought`、`end` 和 `error`，还可能出现其他事件。按 `type` 分支处理，不假设事件集合封闭；`end` 应是成功输出的最后事件。

完成判定至少同时满足：

- 进程已退出且退出码可解释；
- 输出末尾存在 `end`，或失败路径存在 `error`；
- 本轮范围内收到匹配的 Stop 事件，或明确记录为何 hook 不可用；
- 工作区现场状态不再变化。

hook 事件与进程状态冲突时，以失败或待审查处理，不猜测成功。

## 7. 独立审查修改

主编排者在 Grok 结束后重新读取现场，不以执行者总结为证据：

1. 检查版本控制状态和基线是否漂移；
2. 阅读完整 diff，确认只改授权范围；
3. 检查行为、失败路径、文案和安全边界；
4. 运行最新的定向测试，再运行必要的更宽验证；
5. 对用户可见流程执行实际验收；
6. 区分本地实现、测试通过、环境准备和真实发布，不越级宣称。

发现问题时，生成聚焦修复 prompt，包含具体文件、现象、预期行为和复验命令。修复进程完成后，从头重复 diff 审查和新鲜验证。

## 8. 收尾与审计

确认没有仍在运行的 Grok 进程后，执行精确清理：

```bash
bash scripts/grok-stop-hook.sh remove \
  --hooks-dir /absolute/grok-home/hooks \
  --runtime-dir /absolute/runtime \
  --name member-61
```

脚本只删除它创建且所有权校验通过的配置和 handler，默认保留事件日志。最后报告执行者范围、修改文件、独立验证、未完成项以及 hook/进程证据边界。
