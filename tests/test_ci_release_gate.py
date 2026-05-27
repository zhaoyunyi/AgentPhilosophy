from __future__ import annotations

from pathlib import Path


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
    assert "agentphilosophy-sync\" init" in content
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
    assert "gh release create" in publish
    assert "main is not synced to origin" in publish
    assert "dist/release-notes-v${version}.md" in publish
