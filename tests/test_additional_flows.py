from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from agentphilosophy.cli import main
from agentphilosophy.hashing import source_tree_hash


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_copy_tree_source(root: Path) -> None:
    write(
        root / "modules" / "skill-pack" / "module.yaml",
        """
name: skill-pack
description: Skill pack
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: skills
    type: copy_tree
    source: files/
    target: "{{ skill_targets.repo_skills }}/skill-pack/"
    strategy: managed_replace
    on_existing_unmanaged: report_only
""".strip()
        + "\n",
    )
    write(root / "modules" / "skill-pack" / "files" / "SKILL.md", "# Skill\n")
    write(root / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: skill-pack\n")


def create_target(root: Path, modules: list[str] | None = None) -> None:
    module_names = modules or ["skill-pack"]
    write(
        root / ".agentphilosophy.yaml",
        "project_name: Demo\nproject_type: fullstack\nmodules:\n"
        + "".join(f"  - {name}\n" for name in module_names)
        + "skill_targets:\n  repo_skills: skills\nvars: {}\n",
    )


def test_validate_rejects_copy_tree_source_escape(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write(source / "outside" / "SKILL.md", "# Outside\n")
    write(
        source / "modules" / "bad-skill" / "module.yaml",
        """
name: bad-skill
description: Bad skill
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: skills
    type: copy_tree
    source: ../../outside/
    target: skills/bad/
    strategy: managed_replace
""".strip()
        + "\n",
    )
    write(source / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: bad-skill\n")

    assert main(["--source", str(source), "validate"]) == 1


def test_validate_target_rejects_copy_tree_child_output_collision(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(
        source / "modules" / "direct-file" / "module.yaml",
        """
name: direct-file
description: Direct file
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: skill-file
    type: rendered_file
    template: templates/SKILL.md.j2
    target: skills/skill-pack/SKILL.md
    strategy: managed_replace
""".strip()
        + "\n",
    )
    write(source / "modules" / "direct-file" / "templates" / "SKILL.md.j2", "# Direct\n")
    write(
        source / "catalog.yaml",
        "schema_version: 1\nmodules:\n  - name: skill-pack\n  - name: direct-file\n",
    )
    create_target(target, ["skill-pack", "direct-file"])

    assert main(["--source", str(source), "validate", str(target)]) == 1


def test_copy_tree_dry_run_and_apply_preserve_dry_run_boundary(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)

    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0
    assert not (target / "skills" / "skill-pack" / "SKILL.md").exists()

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# Skill\n"


def test_init_only_existing_unmanaged_file_is_skipped_without_state_adoption(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write(
        source / "modules" / "feature-domain" / "module.yaml",
        """
name: feature-domain
description: Feature domain
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: index
    type: rendered_file
    template: templates/README.md.j2
    target: spec/features/README.md
    strategy: init_only
    on_existing_unmanaged: warn
""".strip()
        + "\n",
    )
    write(source / "modules" / "feature-domain" / "templates" / "README.md.j2", "# Generated\n")
    write(source / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: feature-domain\n")
    create_target(target, ["feature-domain"])
    write(target / "spec" / "features" / "README.md", "# User Owned\n")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "spec/features/README.md" not in state_text
    assert (target / "spec" / "features" / "README.md").read_text(encoding="utf-8") == "# User Owned\n"


def test_push_report_only_apply_writes_candidate_not_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write(
        source / "modules" / "report-module" / "module.yaml",
        """
name: report-module
description: Report module
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: report
    type: rendered_file
    template: templates/report.md.j2
    target: spec/Report.md
    strategy: report_only
""".strip()
        + "\n",
    )
    write(source / "modules" / "report-module" / "templates" / "report.md.j2", "# Candidate\n")
    write(source / "catalog.yaml", "schema_version: 1\nmodules:\n  - name: report-module\n")
    create_target(target, ["report-module"])

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    assert not (target / "spec" / "Report.md").exists()
    assert (target / ".agents" / "migration" / "diffs" / "spec__Report.md.new").read_text(
        encoding="utf-8"
    ) == "# Candidate\n"


def test_unmanaged_existing_file_is_not_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    write(target / "skills" / "skill-pack" / "SKILL.md", "# User Skill\n")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# User Skill\n"
    assert (target / ".agents" / "migration" / "diffs" / "skills__skill-pack__SKILL.md.new").exists()


def test_adopt_from_report_registers_multiple_files_without_modifying_content(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    write(target / "skills" / "skill-pack" / "SKILL.md", "# User Skill\n")
    write(
        target / ".agents" / "migration" / "adopt-plan.yaml",
        """
files:
  - path: skills/skill-pack/SKILL.md
    module: skill-pack
    output_id: skills:SKILL.md
""".strip()
        + "\n",
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "adopt",
                str(target),
                "--from-report",
                ".agents/migration/adopt-plan.yaml",
            ]
        )
        == 0
    )
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# User Skill\n"
    assert (target / ".agents" / "agentphilosophy-state.yaml").exists()


def test_adopt_rejects_file_that_does_not_match_output_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    write(target / "wrong" / "SKILL.md", "# Wrong\n")

    assert (
        main(
            [
                "--source",
                str(source),
                "adopt",
                str(target),
                "--file",
                "wrong/SKILL.md",
                "--module",
                "skill-pack",
                "--output",
                "skills:SKILL.md",
            ]
        )
        == 1
    )


def test_push_all_dry_run_uses_registry_without_writing_targets(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    write(
        source / "registry.yaml",
        f"projects:\n  - name: Demo\n    path: {target.as_posix()}\n",
    )

    assert main(["--source", str(source), "push", "--all", "--dry-run"]) == 0
    assert not (target / "skills" / "skill-pack" / "SKILL.md").exists()


def test_push_all_apply_syncs_registry_projects(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    write(
        source / "registry.yaml",
        f"projects:\n  - name: Demo\n    path: {target.as_posix()}\n",
    )

    assert main(["--source", str(source), "push", "--all", "--apply"]) == 0
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# Skill\n"


def test_migrate_generates_candidate_diffs_but_push_requires_formal_config(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(target / "skills" / "skill-pack" / "SKILL.md", "# Legacy\n")

    assert main(["--source", str(source), "migrate", str(target)]) == 0
    assert (target / ".agents" / "migration" / "diffs" / "skills__skill-pack__SKILL.md.new").exists()
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1

    copyfile(
        target / ".agents" / "migration" / "proposed.agentphilosophy.yaml",
        target / ".agentphilosophy.yaml",
    )
    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0


def test_migrate_adopt_plan_includes_copy_tree_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(target / "skills" / "skill-pack" / "SKILL.md", "# Legacy Skill\n")

    assert main(["--source", str(source), "migrate", str(target)]) == 0

    adopt_plan = target / ".agents" / "migration" / "adopt-plan.yaml"
    assert "skills/skill-pack/SKILL.md" in adopt_plan.read_text(encoding="utf-8")

    assert (
        main(
            [
                "--source",
                str(source),
                "adopt",
                str(target),
                "--from-report",
                ".agents/migration/adopt-plan.yaml",
            ]
        )
        == 0
    )
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# Legacy Skill\n"


def test_status_reports_missing_config_stale_module_and_prune_candidate(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    state_path = target / ".agents" / "agentphilosophy-state.yaml"
    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace("skill-pack: 1.0.0", "skill-pack: 0.9.0"),
        encoding="utf-8",
    )
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "module version stale: skill-pack" in output
    assert "managed file can be pruned" in output

    (target / ".agentphilosophy.yaml").unlink()
    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    assert "project config missing" in capsys.readouterr().out


def test_status_reports_manual_edit_and_source_tree_hash_drift(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(target / "skills" / "skill-pack" / "SKILL.md", "# Manual Edit\n")
    write(source / "modules" / "skill-pack" / "files" / "OTHER.md", "# New Source\n")

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "source_tree_hash differs from current source" in output
    assert "managed file changed manually: skills/skill-pack/SKILL.md" in output


def test_unsupported_init_interactive_and_prune_are_not_silent(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)

    assert main(["--source", str(source), "init", str(tmp_path / "new"), "--interactive"]) == 1
    assert "not implemented" in capsys.readouterr().out

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 1
    assert "not implemented" in capsys.readouterr().out


def test_source_tree_hash_excludes_registry_changes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    create_copy_tree_source(source)
    before = source_tree_hash(source)

    write(source / "registry.yaml", "projects: []\n")

    assert source_tree_hash(source) == before
