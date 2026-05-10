from __future__ import annotations

from pathlib import Path

from agentphilosophy.cli import main


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
    write(
        root / "modules" / "doc-templates" / "templates" / "AGENTS.md.j2",
        "# {{ project_name }}\n\n{{ section('model_constraints') }}\n",
    )
    write(
        root / "modules" / "model-constraints" / "module.yaml",
        """
name: model-constraints
description: Model constraints
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: model-rules
    type: fragment
    template: templates/model.md.j2
    target: AGENTS.md
    section: model_constraints
    order: 10
""".strip()
        + "\n",
    )
    write(root / "modules" / "model-constraints" / "templates" / "model.md.j2", "- 使用 {{ primary_tool }}\n")
    write(root / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: doc-templates\n  - name: model-constraints\n")


def create_target(root: Path) -> None:
    write(
        root / ".agentphilosophy.yaml",
        """
project_name: Demo
project_type: fullstack
paths:
  spec_dir: spec
modules:
  - doc-templates
  - model-constraints
vars:
  primary_tool: Codex CLI
""".strip()
        + "\n",
    )


def test_push_dry_run_does_not_write_target_or_state(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    create_target(target)

    exit_code = main(["--source", str(source), "push", str(target), "--dry-run"])

    assert exit_code == 0
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".agents" / "agentphilosophy-state.yaml").exists()


def test_push_apply_writes_managed_file_and_blocks_manual_edits(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_source(source)
    create_target(target)

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Demo\n\n- 使用 Codex CLI\n"
    assert (target / ".agents" / "agentphilosophy-state.yaml").exists()

    write(target / "AGENTS.md", "# Demo\n\n用户手写内容\n")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Demo\n\n用户手写内容\n"
