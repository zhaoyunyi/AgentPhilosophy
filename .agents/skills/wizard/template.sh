#!/usr/bin/env bash
# Wizard 固定库。复制模板后只修改 STAGES 标记以下区域。
set -euo pipefail

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
else
  BOLD=""; DIM=""; RESET=""; BLUE=""; GREEN=""; YELLOW=""
fi

ENV_FILE="${ENV_FILE:-.env}"
TOTAL_STAGES=0
_STAGE_INDEX=0
WRITTEN_ENV=()
WRITTEN_SECRET=()
SKIPPED=()

_clear() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1; then tput clear; else printf '\033[2J\033[3J\033[H'; fi
}

banner() {
  _clear
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  共 %s 个阶段；可随时 Ctrl-C，重新运行会复用已保存值。%s\n\n' "$DIM" "$TOTAL_STAGES" "$RESET"
  pause "准备开始时按 Enter"
}

stage() {
  _clear
  _STAGE_INDEX=$((_STAGE_INDEX + 1))
  printf '\n%s%s▸ 阶段 %s/%s · %s%s\n' "$BOLD" "$BLUE" "$_STAGE_INDEX" "$TOTAL_STAGES" "$1" "$RESET"
}

step() { printf '  %s•%s %s\n' "$BLUE" "$RESET" "$1"; }
say() { printf '  %s\n' "$1"; }
note() { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
warn() { printf '  %s⚠ %s%s\n' "$YELLOW" "$1" "$RESET"; }

open_url() {
  local url="$1"
  printf '  %s↗ 打开%s %s\n' "$GREEN" "$RESET" "$url"
  { if command -v wslview >/dev/null 2>&1; then wslview "$url"
    elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$url"
    elif command -v open >/dev/null 2>&1; then open "$url"
    else warn "无法自动打开浏览器，请手动访问：$url"; fi
  } >/dev/null 2>&1 || warn "无法自动打开浏览器，请手动访问：$url"
}

pause() {
  printf '  %s%s%s ' "$DIM" "${1:-按 Enter 继续}" "$RESET"
  read -r _ || true
}

ask() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[Enter 保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -r input || true
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

ask_secret() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[Enter 保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -rs input || true
  printf '\n'
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

confirm() {
  local prompt="$1" answer
  read -r -p "$prompt [y/N] " answer || true
  answer="${answer:-}"
  [[ "$answer" == "y" || "$answer" == "Y" ]]
}

_existing() {
  [[ -f "$ENV_FILE" ]] || return 1
  local line
  line=$(grep -E "^${1}=" "$ENV_FILE" | tail -n1) || return 1
  printf '%s' "${line#*=}"
}

write_env() {
  local name="$1" value="$2" tmp
  touch "$ENV_FILE"
  tmp=$(mktemp)
  grep -vE "^${name}=" "$ENV_FILE" > "$tmp" || true
  printf '%s=%s\n' "$name" "$value" >> "$tmp"
  mv "$tmp" "$ENV_FILE"
  WRITTEN_ENV+=("$name")
  printf '  %s✓ 写入%s %s → %s\n' "$GREEN" "$RESET" "$name" "$ENV_FILE"
}

set_secret() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1 \
    && printf '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then
    WRITTEN_SECRET+=("$name")
  else
    SKIPPED+=("GitHub Secret $name（手动执行：gh secret set $name）")
    warn "未设置 GitHub Secret $name：gh 尚未就绪"
  fi
}

set_var() {
  local name="$1" value="$2"
  if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1 \
    || ! gh variable set "$name" --body "$value" >/dev/null 2>&1; then
    SKIPPED+=("GitHub Variable $name")
    warn "未设置 GitHub Variable $name：gh 尚未就绪"
  fi
}

finish() {
  _clear
  printf '\n%s%s  ✓ 配置阶段完成%s\n' "$BOLD" "$GREEN" "$RESET"
  ((${#WRITTEN_ENV[@]})) && note "已写入 $ENV_FILE：${WRITTEN_ENV[*]}"
  ((${#WRITTEN_SECRET[@]})) && note "已设置 GitHub Secret：${WRITTEN_SECRET[*]}"
  if ((${#SKIPPED[@]})); then
    warn "仍需人工处理："
    for skipped_item in "${SKIPPED[@]}"; do note "  - $skipped_item"; done
  fi
  printf '\n'
}

# STAGES：复制模板后，只修改本标记以下区域，并使 TOTAL_STAGES 与 stage 数量一致。
TOTAL_STAGES=1
banner "示例配置向导"
stage "示例阶段"
say "用真实步骤替换本示例。"
finish
