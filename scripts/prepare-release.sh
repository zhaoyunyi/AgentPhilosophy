#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/prepare-release.sh VERSION [--content-version VERSION]

Prepare a local AgentPhilosophy release:
  - bump CLI version in pyproject.toml and src/agentphilosophy/__init__.py
  - bump README stable install command tag
  - bump content_version in catalog.yaml and packaged default_source/catalog.yaml
  - refresh uv.lock and this repo's managed state
  - run lint, tests, central-source validation, build, and installed-wheel smoke
  - write dist/release-notes-vVERSION.md

The script does not commit, push, tag, or publish. Use jj commands and then
scripts/publish-release.sh after reviewing the diff.
EOF
}

version=""
content_version=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --content-version)
      content_version="${2:-}"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$version" ]]; then
        echo "Unexpected extra argument: $1" >&2
        usage >&2
        exit 2
      fi
      version="$1"
      shift
      ;;
  esac
done

if [[ -z "$version" ]]; then
  usage >&2
  exit 2
fi

content_version="${content_version:-$version}"

semver_re='^[0-9]+\.[0-9]+\.[0-9]+$'
if [[ ! "$version" =~ $semver_re ]]; then
  echo "VERSION must use MAJOR.MINOR.PATCH: $version" >&2
  exit 2
fi
if [[ ! "$content_version" =~ $semver_re ]]; then
  echo "--content-version must use MAJOR.MINOR.PATCH: $content_version" >&2
  exit 2
fi

if [[ ! -d .jj ]]; then
  echo "This script must run from the AgentPhilosophy jj workspace root." >&2
  exit 2
fi

jj_status="$(jj status)"
if ! grep -q "The working copy has no changes." <<<"$jj_status"; then
  echo "Working copy is not clean; start release preparation from a clean main child." >&2
  echo "$jj_status" >&2
  exit 2
fi

uv run python - "$version" "$content_version" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

version = sys.argv[1]
content_version = sys.argv[2]

replacements = {
    Path("pyproject.toml"): (r'(?m)^version = "[^"]+"$', f'version = "{version}"'),
    Path("src/agentphilosophy/__init__.py"): (
        r'(?m)^__version__ = "[^"]+"$',
        f'__version__ = "{version}"',
    ),
    Path("README.md"): (
        r"AgentPhilosophy\.git@v[0-9]+\.[0-9]+\.[0-9]+",
        f"AgentPhilosophy.git@v{version}",
    ),
    Path("catalog.yaml"): (
        r"(?m)^content_version: .+$",
        f"content_version: {content_version}",
    ),
    Path("src/agentphilosophy/default_source/catalog.yaml"): (
        r"(?m)^content_version: .+$",
        f"content_version: {content_version}",
    ),
}

for path, (pattern, replacement) in replacements.items():
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"failed to update {path}: pattern not found")
    path.write_text(updated, encoding="utf-8")
PY

uv lock
uv run sync.py push . --apply
uv run ruff check .
uv run pytest -q
uv run sync.py validate

mkdir -p dist
uv build
bash scripts/release-smoke.sh "dist/agentphilosophy-${version}-py3-none-any.whl"

mkdir -p dist
cat >"dist/release-notes-v${version}.md" <<EOF
## 变更摘要

- 发布 AgentPhilosophy CLI v${version}。
- 默认内容源 \`content_version\` 升级到 \`${content_version}\`。
- 请补充本次 CLI、内容源、模块或文档的具体变更。

## 依赖项目影响

- \`agentphilosophy_version\` 会写入依赖项目 \`.agents/agentphilosophy-state.yaml\`。
- \`source_content_version\` 用于提示依赖项目是否需要同步新一轮中央内容。
- 发版后运行 \`uv run sync.py status\` 查看 registry 中依赖项目是否 stale。

## 验证

- \`uv run ruff check .\`
- \`uv run pytest -q\`
- \`uv run sync.py validate\`
- \`uv build\`
- \`bash scripts/release-smoke.sh dist/agentphilosophy-${version}-py3-none-any.whl\`
EOF

echo "Prepared AgentPhilosophy release v${version} with content_version ${content_version}."
echo "Review dist/release-notes-v${version}.md before publishing."
