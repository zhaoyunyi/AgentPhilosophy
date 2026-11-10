#!/usr/bin/env bash
set -euo pipefail

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "需要 Gitleaks 8.30.1；工具缺失，扫描未执行。" >&2
  exit 2
fi
if [[ "$(gitleaks version)" != "8.30.1" ]]; then
  echo "需要 Gitleaks 8.30.1；请使用仓库约定版本。" >&2
  exit 2
fi

script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_repository="${1:-.}"

# HEAD 覆盖 PR 的 detached merge 提交；公开分支/tag 覆盖已删除的历史秘密。
# 不接受源码中的行内豁免或调用目录的忽略名单，输出始终遮盖凭据值。
exec gitleaks git "$target_repository" \
  --config "$script_root/.gitleaks.toml" \
  --gitleaks-ignore-path /dev/null \
  --ignore-gitleaks-allow \
  --log-opts="--branches --tags HEAD --full-history" \
  --redact --no-banner
