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
    assert "agentphilosophy-sync\" llm-usage" in content
    assert "agentphilosophy-sync\" init" in content
