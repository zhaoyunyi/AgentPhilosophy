from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from .content import source_files


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_tree_hash(source_root: Path) -> str:
    digest = hashlib.sha256()
    for path in source_files(source_root):
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
