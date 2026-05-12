from __future__ import annotations

from pathlib import Path


def source_files(root: Path) -> list[Path]:
    include_files = [
        root / "catalog.yaml",
        root / "docs" / "cli-usage-for-llm.md",
    ]
    include_dirs = [
        root / "modules",
        root / "presets",
        root / "templates",
    ]

    files = [path for path in include_files if path.is_file()]
    for directory in include_dirs:
        files.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def test_packaged_default_source_matches_repository_source() -> None:
    root = Path(__file__).resolve().parents[1]
    packaged = root / "src" / "agentphilosophy" / "default_source"

    repository_files = [path.relative_to(root).as_posix() for path in source_files(root)]
    packaged_files = [
        path.relative_to(packaged).as_posix()
        for path in source_files(packaged)
    ]

    assert packaged_files == repository_files
    for relative in repository_files:
        assert (packaged / relative).read_bytes() == (root / relative).read_bytes()
