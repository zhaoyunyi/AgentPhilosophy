from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_tree_hash(source_root: Path) -> str:
    digest = hashlib.sha256()
    include_paths = [
        source_root / "catalog.yaml",
        source_root / "docs" / "cli-usage-for-llm.md",
        source_root / "docs" / "llm-usage-auto-config.md",
        source_root / "docs" / "llm-usage-user-breakpoints.md",
        source_root / "docs" / "llm-usage-user-breakpoints.json",
    ]
    include_dirs = [
        source_root / "modules",
        source_root / "presets",
        source_root / "templates",
    ]

    files: list[Path] = [path for path in include_paths if path.is_file()]
    for directory in include_dirs:
        if directory.is_dir():
            files.extend(path for path in directory.rglob("*") if path.is_file())

    for path in sorted(files, key=lambda item: item.relative_to(source_root).as_posix()):
        rel = path.relative_to(source_root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def source_revision(source_root: Path) -> str:
    for command in (
        ["jj", "log", "-r", "@", "--no-graph", "-T", "change_id"],
        ["git", "rev-parse", "HEAD"],
    ):
        try:
            result = subprocess.run(
                command,
                cwd=source_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and result.stdout.strip():
            prefix = "jj:" if command[0] == "jj" else "git:"
            return prefix + result.stdout.strip()
    return "none"
