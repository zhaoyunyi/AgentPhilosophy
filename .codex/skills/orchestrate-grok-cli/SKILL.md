---
name: orchestrate-grok-cli
description: 编排 Grok CLI 单次 headless agent、自动权限、Stop hook、并行隔离任务、进程轮询与独立修改审查；适用于用户要求使用 grok 或 gork headless、自动允许权限、利用 hook 获取结束信号、让多个 Grok CLI 修改并由主 agent 负责编排和审查时。
---

# Grok CLI 编排

把 Grok CLI 当作有边界的执行者，而不是事实裁判。先限定任务和写入范围，再启动 headless 进程；以进程退出和 Stop 事件交叉确认结束，最后由编排者独立审查 diff 与验证结果。

## 执行工作流

1. 读取 [headless-orchestration.md](references/headless-orchestration.md)，确认当前 Grok 版本、headless 入口、权限和 hook 语义。
2. 记录目标仓库的现场基线：工作区状态、提交点、已有 WIP、项目指令和验证命令。不得让 Grok 覆盖未授权改动。
3. 把工作拆成写入范围互不重叠、可独立验收的任务。并行写入时使用隔离工作区；共享工作区只允许一个写入者。
4. 需要结束信号时，使用 `scripts/grok-stop-hook.sh` 在显式的 `.grok/hooks` 目录安装临时 Stop hook。跨多个隔离工作区时优先安装到全局 Grok hooks 目录；单仓任务才使用已信任项目的 hooks 目录。用 `grok inspect` 确认 hook 数量实际增加后再启动执行者。
5. 为每个执行者写独立 prompt 文件，明确 cwd、输入、允许修改的文件、禁止事项、验收标准、验证命令以及“不提交、不推送”的边界。
6. 使用 `grok --prompt-file` 或 `grok -p` 启动一次性 headless 进程；需要无人值守时同时传入 `--always-approve --permission-mode bypassPermissions`，并用 deny 规则、隔离工作区和 prompt 边界限制风险。
7. 轮询每个进程的退出状态和增量输出。Stop hook 是辅助完成信号；进程退出码、`streaming-json` 的 `end`/`error` 事件和限定范围内的 Stop 事件必须相互一致。
8. Grok 结束后由主 agent 独立检查版本控制状态、完整 diff、测试和用户可见行为。不要把 Grok 的总结、自报测试通过或 hook 到达当作验收结论。
9. 审查发现问题时，发送只针对发现项的修复 prompt，再重复结束确认和独立审查。全部通过后精确移除临时 hook 配置和 handler，保留事件日志作为审计线索。

## 强制边界

- `grok agent headless` 是 WebSocket relay，不接收任务 prompt；一次性自动化使用 `--prompt-file`、`--prompt-json` 或 `-p/--single`。
- 自动允许权限只消除 Grok 内部的交互批准，不扩张用户授权；生产变更、外部写入、凭据读取、发布和破坏性操作仍需原请求明确覆盖。
- Stop hook 在真正完成时触发，但全局 hook 可能同时记录其他 Grok 会话；按 cwd、session ID 和本轮时间窗过滤，不能用日志总行数推断自己的任务数。
- `streaming-json` 可能很大；保留原始日志或受控尾部，不把全部推理输出灌入编排上下文。
- 多个 Grok 不得并行修改同一工作区或同一文件。审查者不得复用执行者的结论，必须从现场 diff 和新鲜验证重新判断。
- prompt、hook 事件和 debug 日志不得包含密钥、令牌或不必要的敏感 payload。

## 临时 Stop hook

使用显式绝对路径安装，避免误改全局配置：

```bash
bash scripts/grok-stop-hook.sh install \
  --hooks-dir /absolute/grok-home/hooks \
  --runtime-dir /absolute/path/to/runtime \
  --name task-slug

grok inspect
```

完成后查看状态并精确移除；事件日志默认保留：

```bash
bash scripts/grok-stop-hook.sh status \
  --hooks-dir /absolute/grok-home/hooks \
  --runtime-dir /absolute/path/to/runtime \
  --name task-slug

bash scripts/grok-stop-hook.sh remove \
  --hooks-dir /absolute/grok-home/hooks \
  --runtime-dir /absolute/path/to/runtime \
  --name task-slug
```

全局目录通常是用户 Grok home 下的 `hooks/`，必须先解析成绝对路径再传给脚本。项目 hook 需要目标目录已被 Grok 信任；hook 在会话启动时加载，所以先安装并确认 `grok inspect` 的 Hooks 计数增加，再启动新的 headless 进程。若项目 hook 未出现，先修复 trust，或改用全局 hook，不能继续假设结束信号可用。
