#!/usr/bin/env python3
"""按中央清单刷新包内生成镜像；默认仅检查，不写入。"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentphilosophy.content import source_files  # noqa: E402
from agentphilosophy.paths import resolve_inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    destination = source / "src/agentphilosophy/default_source"
    relative = destination.relative_to(source)
    ancestors = [source.joinpath(*relative.parts[:index]) for index in range(1, len(relative.parts) + 1)]
    if any(path.is_symlink() for path in ancestors):
        parser.error("packaged mirror ancestors must not be symlinks")
    if any(path.is_symlink() for path in destination.rglob("*")):
        parser.error("packaged mirror must contain regular files and directories, not symlinks")
    expected = {p.relative_to(source).as_posix(): p for p in source_files(source)}
    if "catalog.yaml" not in expected:
        parser.error("source must contain catalog.yaml")
    existing = {p.relative_to(destination).as_posix(): p for p in destination.rglob("*")
                if p.is_file() or p.is_symlink()}
    changed = [name for name, path in expected.items()
               if name not in existing or path.read_bytes() != existing[name].read_bytes()]
    removed = sorted(existing.keys() - expected.keys())
    # 先校验全部目标，避免发现后置越界链接时已写入部分镜像。
    for name in {*changed, *removed}:
        resolve_inside(destination, name, label="packaged source")
    for name in changed:
        print(f"{'write' if args.apply else 'stale'}: {name}")
        if args.apply:
            target = resolve_inside(destination, name, label="packaged source")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(expected[name], target)
    for name in removed:
        print(f"{'remove' if args.apply else 'obsolete'}: {name}")
        if args.apply:
            resolve_inside(destination, name, label="packaged source").unlink()
    if not changed and not removed:
        print("packaged source is up to date")
    return 0 if args.apply or not (changed or removed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
