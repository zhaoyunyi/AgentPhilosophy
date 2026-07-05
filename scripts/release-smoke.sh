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
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode user-breakpoints --format json >"$smoke_root/llm-usage-user-breakpoints.json"
grep -q "自动配置安装说明" "$smoke_root/llm-usage-auto-config.md"
grep -q "用户断点配置说明" "$smoke_root/llm-usage-user-breakpoints.md"
"$smoke_root/venv/bin/python" - "$smoke_root/llm-usage-user-breakpoints.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["mode"] == "user-breakpoints"
assert payload["format_version"] == 1
assert payload["breakpoints"][0]["title"]
assert payload["breakpoints"][0]["recommended"]["id"]
assert payload["breakpoints"][0]["options"][0]["id"]
assert payload["breakpoints"][0]["reply_format"]
PY

target="$smoke_root/project"
"$smoke_root/venv/bin/agentphilosophy-sync" init "$target" --preset fullstack >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --apply >/dev/null
grep -q "superpowers-system" "$target/.agentphilosophy.yaml"
grep -q "Superpowers skill 版本为 \`6.0\`" "$target/AGENTS.md"
grep -q "~/.agents/skills/superpowers" "$target/AGENTS.md"
grep -q "skill-ponytail" "$target/.agentphilosophy.yaml"
test -f "$target/skills/ponytail/SKILL.md"
test -f "$target/.codex/skills/ponytail/SKILL.md"
cmp -s \
  "$target/skills/ponytail/SKILL.md" \
  "$target/.codex/skills/ponytail/SKILL.md"
grep -q "DietrichGebert/ponytail" "$target/skills/ponytail/SKILL.md"
test -f "$target/skills/improve-codebase-architecture/SKILL.md"
test -f "$target/.codex/skills/improve-codebase-architecture/SKILL.md"
cmp -s \
  "$target/skills/improve-codebase-architecture/SKILL.md" \
  "$target/.codex/skills/improve-codebase-architecture/SKILL.md"
grep -q "AgentPhilosophy ArchitectureSpec" "$target/skills/improve-codebase-architecture/SKILL.md"

optional_target="$smoke_root/project-with-philosophy-extraction"
mkdir -p "$optional_target"
cat >"$optional_target/.agentphilosophy.yaml" <<'YAML'
project_name: PhilosophyExtractionSmoke
project_type: orchestrator
modules:
  - aphilosophy
  - skill-philosophy-extraction
YAML
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$optional_target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$optional_target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$optional_target" --apply >/dev/null
test -f "$optional_target/skills/philosophy-extraction/SKILL.md"
test -f "$optional_target/.codex/skills/philosophy-extraction/SKILL.md"
cmp -s \
  "$optional_target/skills/philosophy-extraction/SKILL.md" \
  "$optional_target/.codex/skills/philosophy-extraction/SKILL.md"
grep -q "不要直接改托管的 \`aphilosophy/\`" "$optional_target/skills/philosophy-extraction/SKILL.md"

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
