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
    assert "uv venv --python 3.12" in content
    assert "uv pip install --python" in content
    assert "smoke_root=\"$(mktemp -d)\"" in content
    assert "cd \"$smoke_root\"" in content
    assert "expected_agentphilosophy_version=" in content
    assert "import agentphilosophy" in content
    assert "agentphilosophy-sync\" --version" in content
    assert "agentphilosophy-sync\" llm-usage" in content
    assert "agentphilosophy-sync\" init" in content
    assert "expected_content_version=" in content
    assert "importlib.resources import files" in content
    assert "default_source\" / \"catalog.yaml" in content
    assert "agentphilosophy_version: ${expected_agentphilosophy_version}" in content
    assert "source_content_version: ${expected_content_version}" in content
    assert "agentphilosophy_version: 0.1.0" not in content
    assert "source_content_version: 0.2.0" not in content
