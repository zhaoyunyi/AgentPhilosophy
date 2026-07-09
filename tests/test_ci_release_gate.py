from __future__ import annotations

import re
from pathlib import Path


def _read_match(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None, f"{path} missing {pattern}"
    return match.group(1)


def _version_tuple(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    assert len(parts) == 3
    return tuple(int(part) for part in parts)


def test_ci_workflow_runs_release_gate_commands() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = root / ".github" / "workflows" / "ci.yml"

    content = workflow.read_text(encoding="utf-8")

    assert "uv run ruff check ." in content
    assert "uv run pytest -q" in content
    assert "uv run sync.py validate" in content
    assert "uv build" in content
    assert "bash scripts/release-smoke.sh" in content


def test_release_smoke_script_checks_installed_cli_and_state_versions() -> None:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "release-smoke.sh"

    content = script.read_text(encoding="utf-8")

    assert "uv venv --python 3.12" in content
    assert "uv pip install --python" in content
    assert "expected_agentphilosophy_version=" in content
    assert "import agentphilosophy" in content
    assert "agentphilosophy-sync\" --version" in content
    assert "agentphilosophy-sync\" llm-usage" in content
    assert "agentphilosophy-sync\" llm-usage --mode auto-config" in content
    assert "agentphilosophy-sync\" llm-usage --mode user-breakpoints" in content
    assert "agentphilosophy-sync\" llm-usage --mode user-breakpoints --format json" in content
    assert "payload[\"breakpoints\"][0][\"reply_format\"]" in content
    assert "agentphilosophy-sync\" init" in content
    assert "superpowers-system" in content
    assert "Superpowers skill 版本为 \\`6.1.1\\`" in content
    assert "skill-ponytail" in content
    assert "skills/ponytail/SKILL.md" in content
    assert ".codex/skills/ponytail/SKILL.md" in content
    assert "DietrichGebert/ponytail" in content
    assert "skills/improve-codebase-architecture/SKILL.md" in content
    assert ".codex/skills/improve-codebase-architecture/SKILL.md" in content
    assert "AgentPhilosophy ArchitectureSpec" in content
    assert "skill-mattpocock-engineering" in content
    assert "grill-with-docs" in content
    assert "skills/to-spec/SKILL.md" in content
    assert ".codex/skills/to-spec/SKILL.md" in content
    assert "/to-tickets" in content
    assert "skills/to-prd/SKILL.md" in content
    assert ".codex/skills/to-prd/SKILL.md" in content
    assert "/to-issues" in content
    assert "/code-review" in content
    assert "skill-philosophy-extraction" in content
    assert "skills/philosophy-extraction/SKILL.md" in content
    assert ".codex/skills/philosophy-extraction/SKILL.md" in content
    assert "expected_content_version=" in content
    assert "importlib.resources import files" in content
    assert "default_source\" / \"catalog.yaml" in content
    assert "agentphilosophy_version: ${expected_agentphilosophy_version}" in content
    assert "source_content_version: ${expected_content_version}" in content
    assert "agentphilosophy_version: 0.1.0" not in content
    assert "source_content_version: 0.2.0" not in content


def test_release_process_documents_prepare_publish_and_dependency_status() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = root / "docs" / "release-process.md"

    content = doc.read_text(encoding="utf-8")

    assert "bash scripts/prepare-release.sh" in content
    assert "bash scripts/publish-release.sh" in content
    assert "uv run sync.py status" in content
    assert "agentphilosophy_version stale" in content
    assert "source_content_version stale" in content


def test_release_scripts_have_prepare_and_publish_safety_gates() -> None:
    root = Path(__file__).resolve().parents[1]
    prepare = (root / "scripts" / "prepare-release.sh").read_text(encoding="utf-8")
    publish = (root / "scripts" / "publish-release.sh").read_text(encoding="utf-8")

    assert "Working copy is not clean" in prepare
    assert "uv run sync.py push . --apply" in prepare
    assert "uv run ruff check ." in prepare
    assert "uv run pytest -q" in prepare
    assert "bash scripts/release-smoke.sh" in prepare
    assert "scripts/generate-release-notes.py" in prepare
    assert "请补充" not in prepare
    assert "gh release create" in publish
    assert "main is not synced to origin" in publish
    assert "dist/release-notes-v${version}.md" in publish


def test_release_metadata_stays_in_a_publishable_state() -> None:
    root = Path(__file__).resolve().parents[1]

    cli_version = _read_match(root / "pyproject.toml", r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"$')
    package_version = _read_match(
        root / "src" / "agentphilosophy" / "__init__.py",
        r'^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$',
    )
    readme_tag = _read_match(root / "README.md", r"AgentPhilosophy\.git@v([0-9]+\.[0-9]+\.[0-9]+)")
    content_version = _read_match(root / "catalog.yaml", r"^content_version: ([0-9]+\.[0-9]+\.[0-9]+)$")
    packaged_content_version = _read_match(
        root / "src" / "agentphilosophy" / "default_source" / "catalog.yaml",
        r"^content_version: ([0-9]+\.[0-9]+\.[0-9]+)$",
    )
    state_agentphilosophy_version = _read_match(
        root / ".agents" / "agentphilosophy-state.yaml",
        r"^agentphilosophy_version: ([0-9]+\.[0-9]+\.[0-9]+)$",
    )
    state_content_version = _read_match(
        root / ".agents" / "agentphilosophy-state.yaml",
        r"^source_content_version: ([0-9]+\.[0-9]+\.[0-9]+)$",
    )
    assert package_version == cli_version
    assert readme_tag == cli_version
    assert packaged_content_version == content_version
    assert _version_tuple(content_version) <= _version_tuple(cli_version)
    assert state_agentphilosophy_version == cli_version
    assert state_content_version == content_version
