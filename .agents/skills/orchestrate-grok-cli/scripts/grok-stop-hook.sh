#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  grok-stop-hook.sh <install|status|remove> \
    --hooks-dir <绝对路径> \
    --runtime-dir <绝对路径> \
    --name <小写 slug> \
    [--event-log <绝对路径>]

install 创建 Grok 原生 Stop hook 配置和 handler。
status 校验所有权并输出 JSON 状态。
remove 只删除本脚本创建的配置和 handler，保留事件日志。
EOF
}

fail() {
  printf '错误：%s\n' "$*" >&2
  exit 2
}

action="${1:-}"
if [[ -z "$action" ]]; then
  usage
  exit 2
fi
shift

hooks_dir=""
runtime_dir=""
name=""
event_log=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hooks-dir)
      [[ $# -ge 2 ]] || fail "--hooks-dir 缺少参数"
      hooks_dir="$2"
      shift 2
      ;;
    --runtime-dir)
      [[ $# -ge 2 ]] || fail "--runtime-dir 缺少参数"
      runtime_dir="$2"
      shift 2
      ;;
    --name)
      [[ $# -ge 2 ]] || fail "--name 缺少参数"
      name="$2"
      shift 2
      ;;
    --event-log)
      [[ $# -ge 2 ]] || fail "--event-log 缺少参数"
      event_log="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "未知参数：$1"
      ;;
  esac
done

[[ "$action" == "install" || "$action" == "status" || "$action" == "remove" ]] || fail "未知动作：$action"
[[ "$hooks_dir" == /* ]] || fail "--hooks-dir 必须是绝对路径"
[[ "$runtime_dir" == /* ]] || fail "--runtime-dir 必须是绝对路径"
[[ "$name" =~ ^[a-z0-9][a-z0-9-]*$ ]] || fail "--name 必须是小写字母、数字或连字符组成的 slug"

if [[ -z "$event_log" ]]; then
  event_log="$runtime_dir/$name-events.jsonl"
fi
[[ "$event_log" == /* ]] || fail "--event-log 必须是绝对路径"

command -v jq >/dev/null 2>&1 || fail "需要 jq"

config_path="$hooks_dir/$name.json"
handler_path="$runtime_dir/$name-stop-handler.sh"
owner_marker="agentphilosophy-orchestrate-grok-cli:$name"
handler_shell="$(jq -rn --arg value "$handler_path" '$value | @sh')"
log_shell="$(jq -rn --arg value "$event_log" '$value | @sh')"
hook_command="$handler_shell $log_shell"

verify_owned() {
  [[ -f "$config_path" ]] || fail "找不到 hook 配置：$config_path"
  [[ -f "$handler_path" ]] || fail "找不到 hook handler：$handler_path"
  jq -e --arg command "$hook_command" \
    '.hooks.Stop[0].hooks[0].type == "command" and .hooks.Stop[0].hooks[0].command == $command' \
    "$config_path" >/dev/null || fail "hook 配置不属于本次安装或内容已漂移"
  grep -Fq "# $owner_marker" "$handler_path" || fail "hook handler 不属于本次安装或内容已漂移"
}

case "$action" in
  install)
    [[ ! -e "$config_path" ]] || fail "拒绝覆盖已有配置：$config_path"
    [[ ! -e "$handler_path" ]] || fail "拒绝覆盖已有 handler：$handler_path"
    mkdir -p -- "$hooks_dir" "$runtime_dir" "$(dirname "$event_log")"

    apply_handler_patch="$(cat <<EOF
#!/usr/bin/env bash
# $owner_marker
set -euo pipefail

[[ \$# -eq 1 ]] || exit 2
event_log="\$1"
payload="\$(cat)"
printf '%s' "\$payload" | jq -e 'type == "object"' >/dev/null
received_at="\$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
jq -cn \
  --argjson payload "\$payload" \
  --arg received_at "\$received_at" \
  '{
    hook_event_name: (\$payload.hookEventName // \$payload.hook_event_name // "Stop"),
    session_id: (\$payload.sessionId // \$payload.session_id // "unknown"),
    cwd: (\$payload.cwd // \$payload.workspaceRoot // \$payload.workspace_root // "unknown"),
    reason: (\$payload.reason // \$payload.stopReason // \$payload.stop_reason // "completed"),
    timestamp: (\$payload.timestamp // \$received_at)
  }' >> "\$event_log"
EOF
)"
    printf '%s\n' "$apply_handler_patch" > "$handler_path"
    chmod 0700 "$handler_path"
    jq -n --arg command "$hook_command" \
      '{hooks: {Stop: [{hooks: [{type: "command", command: $command, timeout: 30}]}]}}' \
      > "$config_path"
    chmod 0600 "$config_path"
    printf '已安装：%s\n事件日志：%s\n请在启动新会话前运行 grok inspect 确认 hook 已加载。\n' "$config_path" "$event_log"
    ;;
  status)
    verify_owned
    event_count=0
    if [[ -f "$event_log" ]]; then
      event_count="$(wc -l < "$event_log" | tr -d ' ')"
    fi
    jq -n \
      --arg config "$config_path" \
      --arg handler "$handler_path" \
      --arg event_log "$event_log" \
      --argjson event_count "$event_count" \
      '{installed: true, config: $config, handler: $handler, event_log: $event_log, event_count: $event_count}'
    ;;
  remove)
    verify_owned
    rm -f -- "$config_path" "$handler_path"
    printf '已移除配置和 handler；事件日志保留在：%s\n' "$event_log"
    ;;
esac
