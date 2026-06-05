from __future__ import annotations

from pathlib import Path


def source_files(root: Path) -> list[Path]:
    include_files = [
        root / "catalog.yaml",
        root / "docs" / "cli-usage-for-llm.md",
        root / "docs" / "llm-usage-auto-config.md",
        root / "docs" / "llm-usage-user-breakpoints.md",
        root / "docs" / "llm-usage-user-breakpoints.json",
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


def test_default_source_has_no_known_content_merge_artifacts() -> None:
    root = Path(__file__).resolve().parents[1]
    banned_fragments = [
        "└──├──",
        "哲学决策框架——元决策原则、架构设计、治理、认知与权限对齐冲突解决协议哲学决策框架",
        "规则权威边界1",
        "决策原则：局部判断正确不构成违反系统规则的正当理由决策原则",
        "不与已有模板的冲突类型重叠不与已有模板的冲突类型重叠",
        "七个冲突协议",
        "PLACEHOLDER_AUDIT_ACTIONS",
    ]

    offenders: list[str] = []
    content_files = source_files(root) + sorted((root / "docs" / "guides").glob("*.md"))
    for path in content_files:
        if path.suffix not in {".md", ".j2", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in banned_fragments:
            if fragment in text:
                offenders.append(f"{path.relative_to(root)} contains {fragment}")

    assert offenders == []
