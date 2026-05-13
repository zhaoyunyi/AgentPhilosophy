#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/publish-release.sh VERSION

Publish a GitHub release for an already committed and pushed AgentPhilosophy
release. The script expects matching dist artifacts and release notes generated
by scripts/prepare-release.sh.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

version="${1:-}"
if [[ -z "$version" ]]; then
  usage >&2
  exit 2
fi

semver_re='^[0-9]+\.[0-9]+\.[0-9]+$'
if [[ ! "$version" =~ $semver_re ]]; then
  echo "VERSION must use MAJOR.MINOR.PATCH: $version" >&2
  exit 2
fi

tag="v${version}"
wheel="dist/agentphilosophy-${version}-py3-none-any.whl"
sdist="dist/agentphilosophy-${version}.tar.gz"
notes="dist/release-notes-v${version}.md"

for path in "$wheel" "$sdist" "$notes"; do
  if [[ ! -f "$path" ]]; then
    echo "Required release artifact missing: $path" >&2
    exit 2
  fi
done

if [[ -n "$(git tag --list "$tag")" ]]; then
  echo "Local tag already exists: $tag" >&2
  exit 2
fi

if gh release view "$tag" >/dev/null 2>&1; then
  echo "GitHub release already exists: $tag" >&2
  exit 2
fi

jj_status="$(jj status)"
if ! grep -q "The working copy has no changes." <<<"$jj_status"; then
  echo "Working copy is not clean; commit and push the release change first." >&2
  echo "$jj_status" >&2
  exit 2
fi

local_main="$(jj log -r main --no-graph -T 'commit_id')"
remote_main="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
if [[ -z "$remote_main" || "$local_main" != "$remote_main" ]]; then
  echo "main is not synced to origin; push the release change before publishing." >&2
  echo "local main:  ${local_main:-missing}" >&2
  echo "origin main: ${remote_main:-missing}" >&2
  exit 2
fi

gh release create "$tag" \
  "$sdist" \
  "$wheel" \
  --target main \
  --title "AgentPhilosophy ${tag}" \
  --notes-file "$notes"

gh release view "$tag" --json tagName,targetCommitish,url,name,isDraft,isPrerelease,assets
git ls-remote --tags origin "refs/tags/${tag}"
