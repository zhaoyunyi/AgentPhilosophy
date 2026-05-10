from __future__ import annotations

from pathlib import Path

from agentphilosophy.cli import main


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_minimal_source(root: Path) -> None:
    write(
        root / "modules" / "doc-templates" / "module.yaml",
        """
name: doc-templates
description: Document templates
version: 1.0.0
default_strategy: managed_replace
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
    write(
        root / "catalog.yaml",
        """
schema_version: 1
modules:
  - name: doc-templates
    category: docs
    description: Document templates
    project_types: [fullstack]
    outputs:
      - AGENTS.md
    risk: low
""".strip()
        + "\n",
    )
    write(
        root / "presets" / "fullstack.yaml",
        """
name: fullstack
description: Fullstack preset
modules:
  - doc-templates
paths:
  spec_dir: spec
skill_targets:
  repo_skills: skills
""".strip()
        + "\n",
    )


def test_validate_central_source_accepts_minimal_catalog_and_module(tmp_path: Path) -> None:
    create_minimal_source(tmp_path)

    exit_code = main(["--source", str(tmp_path), "validate"])

    assert exit_code == 0


def test_validate_central_source_fails_for_duplicate_output_ids(tmp_path: Path) -> None:
    create_minimal_source(tmp_path)
    module_path = tmp_path / "modules" / "doc-templates" / "module.yaml"
    module_path.write_text(
        module_path.read_text(encoding="utf-8")
        + """
  - id: agents
    type: rendered_file
    template: templates/OTHER.md.j2
    target: OTHER.md
    strategy: managed_replace
""",
        encoding="utf-8",
    )

    exit_code = main(["--source", str(tmp_path), "validate"])

    assert exit_code == 1


def test_validate_target_rejects_output_path_escape_after_template_render(tmp_path: Path) -> None:
    create_minimal_source(tmp_path)
    module_path = tmp_path / "modules" / "doc-templates" / "module.yaml"
    module_path.write_text(
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
    target: "{{ paths.spec_dir }}/../outside.md"
    strategy: managed_replace
    on_existing_unmanaged: report_only
""".strip()
        + "\n",
        encoding="utf-8",
    )
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: BadTarget
project_type: fullstack
paths:
  spec_dir: ../escape
modules:
  - doc-templates
vars: {}
""".strip()
        + "\n",
    )

    exit_code = main(["--source", str(tmp_path), "validate", str(target)])

    assert exit_code == 1
