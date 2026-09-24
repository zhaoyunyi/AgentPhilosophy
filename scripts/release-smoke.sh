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
wheel="$(cd "$(dirname "$wheel")" && pwd)/$(basename "$wheel")"

smoke_root="$(mktemp -d)"
trap 'rm -rf "$smoke_root"' EXIT

uv venv --python "${AGENTPHILOSOPHY_SMOKE_PYTHON:-3.12}" "$smoke_root/venv" >/dev/null
uv pip install --python "$smoke_root/venv/bin/python" "$wheel" >/dev/null

# 从中立目录验证包内内容源，避免源码 checkout 掩盖漏打包资源。
cd "$smoke_root"
"$smoke_root/venv/bin/python" - <<'PY'
from importlib.resources import files

from agentphilosophy.resources import resolve_source_root

with resolve_source_root(None) as source:
    assert source == files("agentphilosophy").joinpath("default_source")
PY

expected_agentphilosophy_version="$("$smoke_root/venv/bin/python" - <<'PY'
import agentphilosophy

print(agentphilosophy.__version__)
PY
)"

"$smoke_root/venv/bin/agentphilosophy-sync" --version | grep -q "${expected_agentphilosophy_version}"
"$smoke_root/venv/bin/code-review-graph" --version | grep -q "2.3.9"
"$smoke_root/venv/bin/agentphilosophy-sync" push --help | grep -q -- "--update-docs"
"$smoke_root/venv/bin/agentphilosophy-sync" push --help | grep -q -- "--llm-command"
"$smoke_root/venv/bin/agentphilosophy-sync" push --help | grep -q -- "--project-name"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage >"$smoke_root/llm-usage.md"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode auto-config >"$smoke_root/llm-usage-auto-config.md"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode user-breakpoints >"$smoke_root/llm-usage-user-breakpoints.md"
"$smoke_root/venv/bin/agentphilosophy-sync" llm-usage --mode user-breakpoints --format json >"$smoke_root/llm-usage-user-breakpoints.json"
grep -q "自动配置安装说明" "$smoke_root/llm-usage-auto-config.md"
grep -q "用户断点配置说明" "$smoke_root/llm-usage-user-breakpoints.md"
grep -q "documentation_paths" "$smoke_root/llm-usage.md"
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
"$smoke_root/venv/bin/python" - "$target/.agentphilosophy.yaml" <<'PY'
import sys

import yaml

config_path = sys.argv[1]
with open(config_path, encoding="utf-8") as handle:
    config = yaml.safe_load(handle)
config.setdefault("vars", {})["matt_implicit_skills"] = [
    "to-spec",
    "to-tickets",
    "implement",
]
with open(config_path, "w", encoding="utf-8") as handle:
    yaml.safe_dump(config, handle, allow_unicode=True, sort_keys=False)
PY
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$target" --apply >/dev/null
! grep -q "superpowers-system" "$target/.agentphilosophy.yaml"
! grep -q "skill-ponytail" "$target/.agentphilosophy.yaml"
grep -q "model-constraints" "$target/.agentphilosophy.yaml"
grep -q "选择合适的模型与推理强度" "$target/AGENTS.md"
! grep -q "Superpowers 可选工作流" "$target/AGENTS.md"
test ! -e "$target/skills/ponytail/SKILL.md"
test ! -e "$target/.agents/skills/ponytail/SKILL.md"
test -f "$target/skills/code-review-graph/SKILL.md"
test -f "$target/.agents/skills/code-review-graph/SKILL.md"
test -f "$target/skills/code-review-graph/CODE-REVIEW-GRAPH-LICENSE.txt"
diff -qr "$target/skills/code-review-graph" "$target/.agents/skills/code-review-graph"
grep -q "MCP 是 agent 的主要查询接口" "$target/skills/code-review-graph/SKILL.md"
grep -q "detect_changes_tool" "$target/skills/code-review-graph/SKILL.md"

superpowers_target="$smoke_root/project-with-superpowers"
mkdir -p "$superpowers_target"
cat >"$superpowers_target/.agentphilosophy.yaml" <<'YAML'
project_name: SuperpowersSmoke
project_type: orchestrator
modules:
  - doc-templates
  - model-constraints
  - superpowers-system
YAML
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$superpowers_target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$superpowers_target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$superpowers_target" --apply >/dev/null
grep -q "当前项目参考 Superpowers \`6.4.1\`" "$superpowers_target/AGENTS.md"
grep -q "~/.agents/skills/superpowers" "$superpowers_target/AGENTS.md"

ponytail_target="$smoke_root/project-with-ponytail"
mkdir -p "$ponytail_target"
cat >"$ponytail_target/.agentphilosophy.yaml" <<'YAML'
project_name: PonytailSmoke
project_type: orchestrator
modules:
  - skill-ponytail
YAML
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$ponytail_target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$ponytail_target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$ponytail_target" --apply >/dev/null
grep -q "skill-ponytail" "$ponytail_target/.agentphilosophy.yaml"
test -f "$ponytail_target/skills/ponytail/SKILL.md"
test -f "$ponytail_target/.agents/skills/ponytail/SKILL.md"
cmp -s \
  "$ponytail_target/skills/ponytail/SKILL.md" \
  "$ponytail_target/.agents/skills/ponytail/SKILL.md"
grep -q "DietrichGebert/ponytail" "$ponytail_target/skills/ponytail/SKILL.md"
grep -q "lite|full|ultra" "$ponytail_target/skills/ponytail/SKILL.md"
test -f "$ponytail_target/skills/ponytail/agents/openai.yaml"
test -f "$ponytail_target/skills/ponytail/PONYTAIL-LICENSE.txt"
diff -qr "$ponytail_target/skills/ponytail" "$ponytail_target/.agents/skills/ponytail"
grep -q "allow_implicit_invocation: true" "$ponytail_target/skills/ponytail/agents/openai.yaml"
test -f "$target/skills/portless-local-dev/PORTLESS-LICENSE.txt"
test -f "$target/skills/portless-local-dev/agents/openai.yaml"
diff -qr "$target/skills/portless-local-dev" "$target/.agents/skills/portless-local-dev"
grep -q "0.15.6" "$target/skills/portless-local-dev/SKILL.md"
grep -q "portless doctor" "$target/skills/portless-local-dev/SKILL.md"
grep -q "dev.example.com" "$target/skills/portless-local-dev/SKILL.md"
grep -q "最长后缀" "$target/skills/portless-local-dev/SKILL.md"
grep -q "不能与 LAN 模式组合" "$target/skills/portless-local-dev/SKILL.md"
test -f "$target/skills/reverse-skill/REVERSE-SKILL-LICENSE.txt"
test -f "$target/skills/reverse-skill/agents/openai.yaml"
diff -qr "$target/skills/reverse-skill" "$target/.agents/skills/reverse-skill"
grep -q "MASTER-ROUTING" "$target/skills/reverse-skill/SKILL.md"
grep -q "Evidence -> Finding -> Path" "$target/skills/reverse-skill/SKILL.md"
test -f "$target/skills/improve-codebase-architecture/SKILL.md"
test -f "$target/.agents/skills/improve-codebase-architecture/SKILL.md"
cmp -s \
  "$target/skills/improve-codebase-architecture/SKILL.md" \
  "$target/.agents/skills/improve-codebase-architecture/SKILL.md"
diff -qr \
  "$target/skills/improve-codebase-architecture" \
  "$target/.agents/skills/improve-codebase-architecture"
grep -q "Copyright (c) 2026 Matt Pocock" \
  "$target/skills/improve-codebase-architecture/MATTPOCOCK-SKILLS-LICENSE.txt"
grep -q "AgentPhilosophy ArchitectureSpec" "$target/skills/improve-codebase-architecture/SKILL.md"
grep -q "skill-mattpocock-engineering" "$target/.agentphilosophy.yaml"
for skill_name in \
  ask-matt triage setup-matt-pocock-skills wayfinder prototype diagnosing-bugs research \
  codebase-design resolving-merge-conflicts grill-me grill-with-docs grilling handoff teach \
  writing-great-skills domain-modeling to-spec to-tickets to-prd to-issues implement tdd code-review; do
  test -f "$target/skills/${skill_name}/SKILL.md"
  test -f "$target/.agents/skills/${skill_name}/SKILL.md"
  diff -qr "$target/skills/${skill_name}" "$target/.agents/skills/${skill_name}"
done
cmp -s \
  "$target/skills/MATTPOCOCK-SKILLS-LICENSE.txt" \
  "$target/.agents/skills/MATTPOCOCK-SKILLS-LICENSE.txt"
grep -q "Copyright (c) 2026 Matt Pocock" "$target/skills/MATTPOCOCK-SKILLS-LICENSE.txt"
test -f "$target/skills/grill-me/SKILL.md"
test -f "$target/.agents/skills/grill-me/SKILL.md"
test -f "$target/.agents/skills/to-spec/SKILL.md"
test -f "$target/.agents/skills/to-prd/SKILL.md"
test -f "$target/skills/to-prd/agents/openai.yaml"
test -f "$target/skills/to-issues/agents/openai.yaml"
grep -q "allow_implicit_invocation: false" "$target/skills/to-prd/agents/openai.yaml"
grep -q "allow_implicit_invocation: false" "$target/skills/to-issues/agents/openai.yaml"
for implicit_skill_name in implement to-spec to-tickets; do
  grep -q "allow_implicit_invocation: true" \
    "$target/skills/${implicit_skill_name}/agents/openai.yaml"
done
test -f "$target/skills/setup-matt-pocock-skills/issue-tracker-local.md"
test -f "$target/skills/triage/AGENT-BRIEF.md"
test -f "$target/skills/diagnosing-bugs/scripts/hitl-loop.template.sh"
test -f "$target/skills/codebase-design/DEEPENING.md"
test -f "$target/skills/prototype/UI.md"
test -f "$target/skills/teach/MISSION-FORMAT.md"
test -f "$target/skills/writing-great-skills/GLOSSARY.md"
grep -q "/grill-with-docs" "$target/skills/grill-with-docs/SKILL.md"
grep -q "/grilling" "$target/skills/grill-me/SKILL.md"
grep -q "/to-spec" "$target/skills/to-spec/SKILL.md"
grep -q "/to-tickets" "$target/skills/to-tickets/SKILL.md"
grep -q "/to-prd" "$target/skills/to-prd/SKILL.md"
grep -q "/to-issues" "$target/skills/to-issues/SKILL.md"
grep -q "/tdd" "$target/skills/implement/SKILL.md"
grep -q "/code-review" "$target/skills/implement/SKILL.md"
test -f "$target/release-notes/README.md"
grep -q "MAJOR.MINOR.PATCH" "$target/AGENTS.md"
grep -q "发布回执" "$target/AGENTS.md"
grep -q "兼容性与迁移" "$target/release-notes/README.md"

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
test -f "$optional_target/.agents/skills/philosophy-extraction/SKILL.md"
cmp -s \
  "$optional_target/skills/philosophy-extraction/SKILL.md" \
  "$optional_target/.agents/skills/philosophy-extraction/SKILL.md"
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
