#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentphilosophy.errors import Report  # noqa: E402
from agentphilosophy.source import load_modules, validate_module_upstream  # noqa: E402


def upstream_refspec(ref: str) -> str:
    if ref == "HEAD" or ref.startswith("refs/"):
        return ref
    return f"refs/heads/{ref}"


def latest_revision(repository: str, ref: str, timeout: int) -> str:
    refspec = upstream_refspec(ref)
    refspecs = [refspec]
    if refspec.startswith("refs/tags/") and not refspec.endswith("^{}"):
        refspecs.append(refspec + "^{}")
    result = subprocess.run(
        ["git", "ls-remote", repository, *refspecs],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git ls-remote failed for {repository}")
    lines = result.stdout.strip().splitlines()
    if not lines:
        raise RuntimeError(f"no revision found for {repository} {ref}")
    peeled = next((line for line in lines if line.endswith("^{}")), lines[0])
    return peeled.split()[0]


@lru_cache(maxsize=128)
def github_data(repository: str, endpoint: str, timeout: int) -> dict | None:
    parsed = urlparse(repository)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise RuntimeError("content/release inspection requires a GitHub HTTPS source; use --refs-only")
    repo = parsed.path.strip("/").removesuffix(".git")
    if len(repo.split("/")) != 2:
        raise RuntimeError("invalid GitHub repository URL")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "AgentPhilosophy-upstream-audit"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com/repos/{repo}/{endpoint}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and endpoint == "releases/latest":
            return None
        raise RuntimeError(f"GitHub {endpoint}: HTTP {exc.code}") from exc


def changed_tracked_paths(repository: str, before: str, after: str, paths: list[str], timeout: int) -> list[str]:
    def tree(revision: str) -> dict[str, str]:
        payload = github_data(repository, f"git/trees/{revision}?recursive=1", timeout)
        if not payload or payload.get("truncated"):
            raise RuntimeError("GitHub tree is missing or truncated; tracked content could not be verified")
        return {
            entry["path"]: entry["sha"] for entry in payload["tree"]
            if entry["type"] != "tree" and any(
                entry["path"] == path.rstrip("/") or entry["path"].startswith(path.rstrip("/") + "/")
                for path in paths
            )
        }
    old, new = tree(before), tree(after)
    return sorted(path for path in old.keys() | new.keys() if old.get(path) != new.get(path))


def iter_upstreams(source_root: Path) -> list[tuple[str, str, str, str]]:
    modules = load_modules(source_root)
    entries: list[tuple[str, str, str, str]] = []
    errors: list[str] = []
    for module in modules.values():
        upstream = module.data.get("upstream")
        if upstream is None:
            continue
        report = Report()
        validate_module_upstream(module, report)
        errors.extend(report.errors)
        if isinstance(upstream, dict) and not report.errors:
            entries.append(
                (
                    module.name,
                    str(upstream["repository"]),
                    str(upstream["ref"]),
                    str(upstream["revision"]),
                )
            )
    if errors:
        raise RuntimeError("\n".join(errors))
    return sorted(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check external upstream revisions recorded by skill modules.")
    parser.add_argument("--source", default=".", help="AgentPhilosophy source root.")
    parser.add_argument("--offline", action="store_true", help="Only list locked revisions; do not contact remotes.")
    parser.add_argument(
        "--refs-only", action="store_true", help="Only compare refs; do not infer content/release freshness.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--timeout", type=int, default=20, help="git ls-remote timeout in seconds.")
    args = parser.parse_args(argv)

    if args.timeout <= 0:
        print("[error] --timeout must be greater than 0", file=sys.stderr)
        return 1

    source_root = Path(args.source).expanduser().resolve()
    stale = False
    failed = False
    try:
        entries = iter_upstreams(source_root)
    except Exception as exc:  # noqa: BLE001
        for line in str(exc).splitlines() or [str(exc)]:
            print(f"[error] {line}", file=sys.stderr)
        return 1

    modules = load_modules(source_root)
    results = [{"module": module.name, "status": module.data.get("source_kind", "untracked")}
               for module in modules.values() if not module.data.get("upstream")]
    revisions = {}
    for module_name, repository, ref, revision in entries:
        record = {"module": module_name, "repository": repository, "ref": ref, "locked_revision": revision,
                  "status": "locked", "changed_paths": None, "latest_release": None, "release_changed": None}
        results.append(record)
        if args.offline:
            continue
        try:
            key = (repository, ref)
            if key not in revisions:
                revisions[key] = latest_revision(repository, ref, args.timeout)
            latest = revisions[key]
            record["latest_revision"] = latest
            record["status"] = "current" if latest == revision else "ref_changed"
            if args.refs_only:
                stale |= latest != revision
                continue
            upstream = modules[module_name].data["upstream"]
            changed = [] if latest == revision else changed_tracked_paths(
                repository, revision, latest, upstream["tracked_paths"], args.timeout,
            )
            record["changed_paths"] = changed
            release = github_data(repository, "releases/latest", args.timeout)
            record["latest_release"] = release.get("tag_name") if release else None
            locked_release = upstream.get("release")
            if ref.startswith("refs/tags/"):
                locked_release = ref.removeprefix("refs/tags/").removesuffix("^{}")
            if locked_release and release:
                record["release_changed"] = locked_release != release.get("tag_name")
            if changed:
                record["status"] = "content_changed"
            elif record["release_changed"]:
                record["status"] = "release_available"
            stale |= bool(changed or record["release_changed"])
        except Exception as exc:  # noqa: BLE001
            failed = True
            record.update(status="error", error=str(exc))
    results.sort(key=lambda item: item["module"])
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not entries:
            print("[info] no upstream metadata found")
        for record in results:
            status, name = record["status"], record["module"]
            if status == "error":
                print(f"[error] {name}: {record['error']}", file=sys.stderr)
            elif "repository" not in record:
                print(f"[info] {name}: {status} source")
            elif args.offline:
                print(f"[info] {name}: {record['repository']} {record['ref']} locked {record['locked_revision']}")
            elif args.refs_only:
                label = "ok" if status == "current" else "stale"
                print(f"[{label}] {name}: {record['repository']} {record['ref']} "
                      f"{record['locked_revision']} -> {record['latest_revision']} (ref only)")
            else:
                print(f"[{status}] {name}: tracked_changes={len(record['changed_paths'])}; "
                      f"latest_release={record['latest_release'] or 'not available'}")
    return 1 if failed else 2 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
