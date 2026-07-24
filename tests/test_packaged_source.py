from __future__ import annotations

import re
from pathlib import Path

from agentphilosophy.yamlio import read_yaml


def source_files(root: Path) -> list[Path]:
    def is_source_file(path: Path) -> bool:
        return path.is_file() and path.name != ".DS_Store"

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

    files = [path for path in include_files if is_source_file(path)]
    for directory in include_dirs:
        files.extend(path for path in directory.rglob("*") if is_source_file(path))
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


def test_optional_skill_uninstall_docs_apply_before_prune() -> None:
    root = Path(__file__).resolve().parents[1]
    usage = (root / "docs" / "cli-usage-for-llm.md").read_text(encoding="utf-8")

    uninstall_section = usage.split("需要卸载已安装的 Ponytail 时", 1)[1].split("## 八、", 1)[0]
    dry_run_index = uninstall_section.index("`push /path/to/project --dry-run`")
    apply_index = uninstall_section.index("`push /path/to/project --apply`")
    prune_index = uninstall_section.index("`push /path/to/project --prune-managed`")

    assert dry_run_index < apply_index < prune_index
    assert "apply 失败时不要 prune" in uninstall_section


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


def test_optimize_build_pipeline_module_is_packaged_with_complete_resources() -> None:
    root = Path(__file__).resolve().parents[1]
    relative_root = Path("modules/skill-optimize-build-pipeline/optimize-build-pipeline")
    repository_skill = root / relative_root
    packaged_skill = root / "src/agentphilosophy/default_source" / relative_root
    expected = {
        "SKILL.md",
        "agents/openai.yaml",
        "references/measurement-contract.md",
        "references/optimization-playbook.md",
        "scripts/analyze_timeline.py",
    }
    repository_files = {
        path.relative_to(repository_skill).as_posix()
        for path in repository_skill.rglob("*")
        if path.is_file()
    }
    packaged_files = {
        path.relative_to(packaged_skill).as_posix()
        for path in packaged_skill.rglob("*")
        if path.is_file()
    }
    assert repository_files == expected
    assert packaged_files == expected


def test_external_skill_modules_declare_upstream_tracking_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    external_skill_modules = {
        "skill-code-review",
        "skill-ponytail",
        "skill-portless-local-dev",
        "skill-improve-codebase-architecture",
        "skill-mattpocock-engineering",
        "skill-reverse-skill",
    }

    for module_name in sorted(external_skill_modules):
        module_yaml = root / "modules" / module_name / "module.yaml"
        data = read_yaml(module_yaml)
        upstream = data.get("upstream")
        assert isinstance(upstream, dict), f"{module_name} missing upstream metadata"
        assert str(upstream.get("repository", "")).startswith("https://github.com/")
        assert upstream.get("ref")
        assert re.fullmatch(r"[0-9a-f]{40}", str(upstream.get("revision", "")))
        assert upstream.get("tracked_paths")


def test_updated_external_skill_modules_lock_reviewed_upstream_revisions() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = {
        "skill-ponytail": ("1.1.0", "16f29800fd2681bdf24f3eb4ccffe38be3baec6b"),
        "skill-portless-local-dev": ("1.3.0", "e0c2af5734fcdc2f6c6992423a023d8ec0c68e26"),
        "skill-reverse-skill": ("1.1.0", "b8ae07db073783597b11f60fa2e900e3f9b9163f"),
    }

    for module_name, (version, revision) in expected.items():
        data = read_yaml(root / "modules" / module_name / "module.yaml")
        assert data["version"] == version
        assert data["upstream"]["revision"] == revision
        assert "LICENSE" in data["upstream"]["tracked_paths"]


def test_long_lived_docs_are_listed_in_docs_index() -> None:
    root = Path(__file__).resolve().parents[1]
    index = root / "docs" / "README.md"

    assert index.is_file()
    index_text = index.read_text(encoding="utf-8")

    docs = sorted(
        path
        for path in (root / "docs").rglob("*.md")
        if path.name != "README.md"
    )
    missing = [
        path.relative_to(root).as_posix()
        for path in docs
        if path.relative_to(root).as_posix() not in index_text
    ]

    assert missing == []
