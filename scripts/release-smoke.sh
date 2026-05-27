#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/release-smoke.sh [dist/agentphilosophy-X.Y.Z-py3-none-any.whl]

Install a built AgentPhilosophy wheel in a temporary Python 3.12 virtualenv and
verify the installed CLI can render a project state with matching CLI/content
versions.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

wheel="${1:-}"
if [[ -z "$wheel" ]]; then
  wheel_count="$(find dist -maxdepth 1 -name 'agentphilosophy-*.whl' -type f | wc -l | tr -d ' ')"
  if [[ "$wheel_count" != "1" ]]; then
    echo "Expected exactly one dist/agentphilosophy-*.whl; pass the wheel path explicitly." >&2
    exit 2
  fi
  wheel="$(find dist -maxdepth 1 -name 'agentphilosophy-*.whl' -type f | sort | sed -n '1p')"
fi

if [[ ! -f "$wheel" ]]; then
  echo "Wheel not found: $wheel" >&2
  exit 2
fi

smoke_root="$(mktemp -d)"
trap 'rm -rf "$smoke_root"' EXIT

uv venv --python 3.12 "$smoke_root/venv" >/dev/null
uv pip install --python "$smoke_root/venv/bin/python" "$wheel" >/dev/null

expected_agentphilosophy_version="$("$smoke_root/venv/bin/python" - <<'PY'
import agentphilosophy

print(agentphilosophy.__version__)
PY
)"

"$smoke_root/venv/bin/agentphilosophy-sync" --version | grep -q "${expected_agentphilosophy_version}"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage >"$smoke_root/llm-usage.md"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode auto-config >"$smoke_root/llm-usage-auto-config.md"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode user-breakpoints >"$smoke_root/llm-usage-user-breakpoints.md"
grep -q "自动配置安装说明" "$smoke_root/llm-usage-auto-config.md"
grep -q "用户断点配置说明" "$smoke_root/llm-usage-user-breakpoints.md"

target="$smoke_root/project"
"$smoke_root/venv/bin/agentphilosophy-sync" init "$target" --preset fullstack >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --apply >/dev/null

expected_content_version="$("$smoke_root/venv/bin/python" - <<'PY'
from importlib.resources import files

import yaml

catalog = yaml.safe_load((files("agentphilosophy") / "default_source" / "catalog.yaml").read_text(encoding="utf-8"))
print(catalog["content_version"])
PY
)"

grep -q "agentphilosophy_version: ${expected_agentphilosophy_version}" "$target/.agents/agentphilosophy-state.yaml"
grep -q "source_content_version: ${expected_content_version}" "$target/.agents/agentphilosophy-state.yaml"
"$smoke_root/venv/bin/agentphilosophy-sync" status --project "$target"

echo "release smoke ok: agentphilosophy=${expected_agentphilosophy_version}, content=${expected_content_version}"
