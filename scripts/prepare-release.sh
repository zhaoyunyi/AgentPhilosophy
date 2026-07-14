#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/prepare-release.sh VERSION [--content-version VERSION]

Prepare a local AgentPhilosophy release:
  - bump CLI version in pyproject.toml and src/agentphilosophy/__init__.py
  - bump content_version in catalog.yaml and packaged default_source/catalog.yaml
  - refresh uv.lock and this repo's managed state
  - run lint, tests, central-source validation, build, and installed-wheel smoke
  - write dist/release-notes-vVERSION.md

The script does not update the README stable install tag, commit, push, tag, or publish.
Use jj commands and then scripts/publish-release.sh after reviewing the diff; update
the README stable tag only after the GitHub Release exists.
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
uv run python scripts/generate-release-notes.py "$version" --content-version "$content_version"

echo "Prepared AgentPhilosophy release v${version} with content_version ${content_version}."
echo "Review dist/release-notes-v${version}.md before publishing."
