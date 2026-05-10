from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_source(root: Path) -> None:
    write(
        root / "modules" / "doc-templates" / "module.yaml",
        """
name: doc-templates
description: Document templates
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: agents
    type: rendered_file
    template: templates/AGENTS.md.j2
    target: AGENTS.md
    strategy: managed_replace
    on_existing_unmanaged: report_only
""".strip()
        + "\n",
    )
    write(root / "modules" / "doc-templates" / "templates" / "AGENTS.md.j2", "# {{ project_name }}\n")
    write(root / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: doc-templates\n")
    write(root / "presets" / "fullstack.yaml", "name: fullstack\nmodules:\n  - doc-templates\n")


def test_e2e_validate_init_push_apply_and_status(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)

    commands = [
        ["validate"],
        ["init", str(target), "--preset", "fullstack"],
        ["push", str(target), "--dry-run"],
        ["push", str(target), "--apply"],
        ["status", "--project", str(target)],
    ]

    for args in commands:
        result = subprocess.run(
            [sys.executable, "sync.py", "--source", str(source), *args],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# target\n"
