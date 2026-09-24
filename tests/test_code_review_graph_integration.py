from __future__ import annotations

import tomllib
from pathlib import Path


def test_package_pins_and_reexports_code_review_graph_cli() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

    assert "code-review-graph==2.3.9" in pyproject["project"]["dependencies"]
    assert pyproject["project"]["scripts"]["code-review-graph"] == "code_review_graph.cli:main"


def test_repository_ignores_local_code_review_graph_database() -> None:
    root = Path(__file__).resolve().parents[1]
    ignore_lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".code-review-graph/" in ignore_lines
