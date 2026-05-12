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


def test_current_model_constraints_extra_rules_render_as_compact_markdown_list(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1]
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: Demo
project_type: orchestrator
modules:
  - doc-templates
  - model-constraints
vars:
  primary_tool: Codex CLI
  extra_model_rules:
    - 使用中文交流和回复。
    - 文档使用中文 Markdown 格式。
""".strip()
        + "\n",
    )

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "- 使用中文交流和回复。\n- 文档使用中文 Markdown 格式。" in agents_text


def test_fullstack_preset_defaults_to_jj_management_with_install_guidance(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1]
    target = tmp_path / "target"

    assert main(["--source", str(source), "init", str(target), "--preset", "fullstack"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    jj_skill_text = (target / "skills" / "jj-management" / "SKILL.md").read_text(encoding="utf-8")
    philosophy_text = (target / "aphilosophy" / "meta-decision-principles.md").read_text(encoding="utf-8")

    assert "- jj-conventions" in project_config
    assert "- skill-jj-management" in project_config
    assert "- aphilosophy" in project_config
    assert "默认使用 jj colocated git 管理当前仓库" in agents_text
    assert "command -v jj" in agents_text
    assert "jj git init --colocate" in agents_text
    assert "安装 jj CLI" in jj_skill_text
    assert "jj git init --colocate" in jj_skill_text
    assert "Agent 元决策原则" in philosophy_text


def test_current_source_does_not_keep_stale_migration_candidates() -> None:
    source = Path(__file__).resolve().parents[1]
    migration_diffs = source / ".agents" / "migration" / "diffs"

    candidates = sorted(path.relative_to(source).as_posix() for path in migration_diffs.glob("*.new"))

    assert candidates == []
