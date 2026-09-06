import subprocess
import sys
from pathlib import Path

import pytest

from agentphilosophy.errors import SyncError
from agentphilosophy.hashing import source_tree_hash


@pytest.mark.parametrize("noise", ["modules/.DS_Store", "modules/probe/__pycache__/tool.pyc"])
def test_content_fingerprint_ignores_local_metadata(tmp_path: Path, noise: str) -> None:
    (tmp_path / "catalog.yaml").write_text("content_version: 0.1.0\n")
    before = source_tree_hash(tmp_path)
    path = tmp_path / noise
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"local machine metadata")
    assert source_tree_hash(tmp_path) == before


def test_distributed_guide_changes_the_content_fingerprint(tmp_path: Path) -> None:
    guide = tmp_path / "docs/guides/code-review-graph.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("First contract\n")
    before = source_tree_hash(tmp_path)
    guide.write_text("Updated contract\n")
    assert source_tree_hash(tmp_path) != before


def test_directory_symlinks_cannot_hide_content_from_the_fingerprint(tmp_path: Path) -> None:
    shared = tmp_path / "shared/probe"
    shared.mkdir(parents=True)
    (shared / "module.yaml").write_text("name: probe\noutputs: []\n")
    (tmp_path / "modules").mkdir()
    (tmp_path / "modules/probe").symlink_to(shared)
    with pytest.raises(SyncError, match="directory symlink"):
        source_tree_hash(tmp_path)


def test_mirror_check_and_apply_remove_unlisted_resources(tmp_path: Path) -> None:
    (tmp_path / "catalog.yaml").write_text("content_version: 0.1.0\n")
    script = Path(__file__).resolve().parents[1] / "scripts/sync-packaged-source.py"
    command = [sys.executable, str(script), "--source", str(tmp_path)]
    assert subprocess.run([*command, "--apply"], capture_output=True).returncode == 0
    mirror = tmp_path / "src/agentphilosophy/default_source"
    noise = [mirror / "unlisted.txt", mirror / "__pycache__/internal.pyc"]
    for path in noise:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not distributed")
    assert subprocess.run([*command, "--check"], capture_output=True).returncode == 1
    assert subprocess.run([*command, "--apply"], capture_output=True).returncode == 0
    assert all(not path.exists() for path in noise)
    assert (mirror / "catalog.yaml").read_bytes() == (tmp_path / "catalog.yaml").read_bytes()


def test_mirror_symlink_is_rejected_before_any_file_is_changed(tmp_path: Path) -> None:
    (tmp_path / "catalog.yaml").write_text("content_version: 0.1.0\n")
    script = Path(__file__).resolve().parents[1] / "scripts/sync-packaged-source.py"
    command = [sys.executable, str(script), "--source", str(tmp_path)]
    assert subprocess.run([*command, "--apply"], capture_output=True).returncode == 0
    mirror = tmp_path / "src/agentphilosophy/default_source"
    (mirror / "obsolete.txt").symlink_to(mirror / "catalog.yaml")
    original = (mirror / "catalog.yaml").read_bytes()
    assert subprocess.run([*command, "--apply"], capture_output=True).returncode != 0
    assert (mirror / "catalog.yaml").read_bytes() == original
    assert (mirror / "obsolete.txt").is_symlink()
