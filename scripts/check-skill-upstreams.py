#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentphilosophy.errors import Report  # noqa: E402
from agentphilosophy.source import load_modules, validate_module_upstream  # noqa: E402


def upstream_refspec(ref: str) -> str:
    if ref == "HEAD" or ref.startswith("refs/"):
        return ref
    return f"refs/heads/{ref}"


def latest_revision(repository: str, ref: str, timeout: int) -> str:
    result = subprocess.run(
        ["git", "ls-remote", repository, upstream_refspec(ref)],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git ls-remote failed for {repository}")
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not first_line:
        raise RuntimeError(f"no revision found for {repository} {ref}")
    return first_line.split()[0]


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
    parser.add_argument("--timeout", type=int, default=20, help="git ls-remote timeout in seconds.")
    args = parser.parse_args(argv)

    if args.timeout <= 0:
        print("[error] --timeout must be greater than 0", file=sys.stderr)
        return 1

    source_root = Path(args.source).expanduser().resolve()
    stale = False
    try:
        entries = iter_upstreams(source_root)
    except Exception as exc:  # noqa: BLE001
        for line in str(exc).splitlines() or [str(exc)]:
            print(f"[error] {line}", file=sys.stderr)
        return 1

    if not entries:
        print("[info] no upstream metadata found")
        return 0

    for module_name, repository, ref, revision in entries:
        if args.offline:
            print(f"[info] {module_name}: {repository} {ref} locked {revision}")
            continue
        try:
            latest = latest_revision(repository, ref, args.timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {module_name}: {exc}", file=sys.stderr)
            return 1
        if latest == revision:
            print(f"[ok] {module_name}: {repository} {ref} {revision}")
        else:
            stale = True
            print(f"[stale] {module_name}: {repository} {ref} {revision} -> {latest}")

    return 2 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
