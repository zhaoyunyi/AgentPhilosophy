from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from agentphilosophy.cli import main


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_central_source(root: Path) -> None:
    write(
        root / "modules" / "doc-templates" / "module.yaml",
        """
name: doc-templates
description: Document templates
version: 1.0.0
project_types: [mobile-sdk]
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
    write(root / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: doc-templates\n")
    write(
        root / "presets" / "mobile-sdk.yaml",
        """
name: mobile-sdk
description: Mobile SDK preset
modules:
  - doc-templates
paths:
  docs_guide_dir: docs/guide
  spec_dir: spec
skill_targets:
  repo_skills: skills
""".strip()
        + "\n",
    )


def test_bdd_new_project_init_then_dry_run_keeps_formal_files_untouched(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "new-project"
    seed_central_source(source)

    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert (target / ".agentphilosophy.yaml").exists()

    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0
    assert not (target / "AGENTS.md").exists()


def test_bdd_old_project_migrate_adopt_then_manual_edit_conflict(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "old-project"
    seed_central_source(source)
    write(target / "AGENTS.md", "# Legacy\n\n旧项目规则\n")

    assert main(["--source", str(source), "migrate", str(target)]) == 0
    assert (target / ".agents" / "migration" / "inventory.md").exists()
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Legacy\n\n旧项目规则\n"
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1

    copyfile(
        target / ".agents" / "migration" / "proposed.agentphilosophy.yaml",
        target / ".agentphilosophy.yaml",
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "adopt",
                str(target),
                "--file",
                "AGENTS.md",
                "--module",
                "doc-templates",
                "--output",
                "agents",
            ]
        )
        == 0
    )
    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Legacy\n\n旧项目规则\n"

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# old-project\n"

    write(target / "AGENTS.md", "# old-project\n\n手动追加\n")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1


def test_bdd_push_apply_reconciles_state_when_manual_file_matches_candidate(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "managed-project"
    seed_central_source(source)

    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(
        source / "modules" / "doc-templates" / "templates" / "AGENTS.md.j2",
        "# {{ project_name }}\n\n新版规则\n",
    )
    write(target / "AGENTS.md", "# managed-project\n\n新版规则\n")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# managed-project\n\n新版规则\n"

    write(target / "AGENTS.md", "# managed-project\n\n手动追加\n")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
