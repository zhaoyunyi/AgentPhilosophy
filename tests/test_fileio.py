from __future__ import annotations

from pathlib import Path

import pytest

from agentphilosophy.fileio import write_bytes_atomic


def test_write_bytes_atomic_leaves_existing_file_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "managed.md"
    target.write_text("old\n", encoding="utf-8")

    def fail_replace(self: Path, target_path: Path) -> Path:
        raise OSError(f"cannot replace {target_path}")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError):
        write_bytes_atomic(target, b"new\n")

    assert target.read_text(encoding="utf-8") == "old\n"
    assert list(tmp_path.glob(".managed.md.*.tmp")) == []


def test_write_bytes_atomic_preserves_existing_file_mode(tmp_path: Path) -> None:
    target = tmp_path / "managed.sh"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o755)

    write_bytes_atomic(target, b"echo managed\n")

    assert target.read_text(encoding="utf-8") == "echo managed\n"
    assert target.stat().st_mode & 0o777 == 0o755
