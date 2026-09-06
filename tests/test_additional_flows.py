from __future__ import annotations

import json
from pathlib import Path
from shutil import copyfile

import pytest

import agentphilosophy.commands as command_module
from agentphilosophy import __version__
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
    write(root / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: skill-pack\n")


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
    write(source / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: bad-skill\n")

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
        "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: skill-pack\n  - name: direct-file\n",
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
    write(source / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: feature-domain\n")
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
    write(source / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: report-module\n")
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
    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert f"agentphilosophy_version: {__version__}" in state_text
    assert "source_content_version: 0.2.0" in state_text


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


def test_push_all_project_name_updates_only_selected_registry_project(tmp_path: Path) -> None:
    source = tmp_path / "source"
    selected = tmp_path / "selected"
    untouched = tmp_path / "untouched"
    create_copy_tree_source(source)
    create_target(selected)
    create_target(untouched)
    write(
        source / "registry.yaml",
        "projects:\n"
        f"  - name: selected\n    path: {selected.as_posix()}\n"
        f"  - name: untouched\n    path: {untouched.as_posix()}\n",
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--project-name",
                "selected",
            ]
        )
        == 0
    )
    assert (selected / "skills" / "skill-pack" / "SKILL.md").exists()
    assert not (untouched / "skills" / "skill-pack" / "SKILL.md").exists()


def test_push_all_project_name_reports_unknown_registry_project(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    create_copy_tree_source(source)
    write(source / "registry.yaml", "projects: []\n")

    assert main(["--source", str(source), "push", "--all", "--dry-run", "--project-name", "missing"]) == 1
    assert "registry project not found: missing" in capsys.readouterr().out


def test_push_all_continues_after_project_sync_io_error(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    failing = tmp_path / "failing"
    succeeding = tmp_path / "succeeding"
    create_copy_tree_source(source)
    create_target(failing)
    create_target(succeeding)
    write(
        source / "registry.yaml",
        "projects:\n"
        f"  - name: failing\n    path: {failing.as_posix()}\n"
        f"  - name: succeeding\n    path: {succeeding.as_posix()}\n",
    )
    real_command_push = command_module.command_push

    def command_push_with_io_error(source_root: Path, project_root: Path, *, apply: bool):
        if project_root == failing:
            raise OSError("simulated write failure")
        return real_command_push(source_root, project_root, apply=apply)

    monkeypatch.setattr(command_module, "command_push", command_push_with_io_error)

    assert main(["--source", str(source), "push", "--all", "--apply"]) == 1
    assert (succeeding / "skills" / "skill-pack" / "SKILL.md").exists()


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
    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace(
            "source_content_version: 0.2.0",
            "source_content_version: 0.1.0",
        ),
        encoding="utf-8",
    )
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "source_content_version stale: 0.1.0 -> 0.2.0" in output
    assert "module version stale: skill-pack" in output
    assert "managed file can be pruned" in output

    (target / ".agentphilosophy.yaml").unlink()
    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    assert "project config missing" in capsys.readouterr().out


def test_status_reports_newer_state_content_version_without_stale(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    state_path = target / ".agents" / "agentphilosophy-state.yaml"
    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace(
            "source_content_version: 0.2.0",
            "source_content_version: 0.3.0",
        ),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "source_content_version newer than current source: 0.3.0 -> 0.2.0" in output
    assert "source_content_version stale" not in output


def test_status_reports_agentphilosophy_version_drift(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    state_path = target / ".agents" / "agentphilosophy-state.yaml"
    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace(
            f"agentphilosophy_version: {__version__}",
            "agentphilosophy_version: 0.1.0",
        ),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert f"agentphilosophy_version stale: 0.1.0 -> {__version__}" in output


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


def test_status_warns_when_managed_file_is_replaced_by_directory(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    managed_file = target / "skills" / "skill-pack" / "SKILL.md"
    managed_file.unlink()
    managed_file.mkdir()

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "managed file is not a regular file: skills/skill-pack/SKILL.md" in output


def test_registry_status_runs_real_project_health_checks(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(target / "skills" / "skill-pack" / "SKILL.md", "# Manual Edit\n")
    write(
        source / "registry.yaml",
        f"projects:\n  - name: Demo\n    path: {target.as_posix()}\n",
    )

    assert main(["--source", str(source), "status"]) == 0

    output = capsys.readouterr().out
    assert "Demo: managed file changed manually: skills/skill-pack/SKILL.md" in output
    assert f"Demo: status checked: {target}" in output


def test_status_ignores_revision_drift_when_source_tree_hash_matches(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    state_path = target / ".agents" / "agentphilosophy-state.yaml"
    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace("source_revision: none", "source_revision: git:old"),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    output = capsys.readouterr().out
    assert "source_tree_hash differs from current source" not in output
    assert "source_revision differs from current source" not in output


def test_init_interactive_creates_config_from_prompts(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    target = tmp_path / "new"
    create_copy_tree_source(source)
    write(
        source / "presets" / "fullstack.yaml",
        """
name: fullstack
description: Fullstack preset
modules:
  - skill-pack
paths:
  docs_guide_dir: docs/guides
skill_targets:
  repo_skills: skills
vars:
  primary_tool: Codex CLI
""".strip()
        + "\n",
    )
    answers = iter(["fullstack", "PromptedName", "fullstack", "Prompted description", "pytest -q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert main(["--source", str(source), "init", str(target), "--interactive"]) == 0

    config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    assert "project_name: PromptedName" in config
    assert "project_type: fullstack" in config
    assert "description: Prompted description" in config
    assert "test_command: pytest -q" in config
    assert "skill-pack" in config


def test_llm_usage_prints_mode_specific_documents(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    write(source / "docs" / "cli-usage-for-llm.md", "# Full usage\n")
    write(source / "docs" / "llm-usage-auto-config.md", "# Auto config usage\n")
    write(source / "docs" / "llm-usage-user-breakpoints.md", "# Breakpoint config usage\n")

    assert main(["--source", str(source), "llm-usage"]) == 0
    assert capsys.readouterr().out == "# Full usage\n"

    assert main(["--source", str(source), "llm-usage", "--mode", "auto-config"]) == 0
    assert capsys.readouterr().out == "# Auto config usage\n"

    assert main(["--source", str(source), "llm-usage", "--mode", "user-breakpoints"]) == 0
    assert capsys.readouterr().out == "# Breakpoint config usage\n"


def test_llm_usage_prints_user_breakpoints_json_format(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    write(source / "docs" / "llm-usage-user-breakpoints.md", "# Breakpoint config usage\n")
    write(
        source / "docs" / "llm-usage-user-breakpoints.json",
        json.dumps(
            {
                "mode": "user-breakpoints",
                "format_version": 1,
                "breakpoints": [
                    {
                        "id": "preset-selection",
                        "title": "选择 preset",
                        "recommended": {
                            "id": "fullstack",
                            "reason": "项目包含 Web、API 或部署入口。",
                        },
                        "options": [
                            {
                                "id": "fullstack",
                                "label": "前后端或部署项目",
                                "impact": "写入 fullstack preset 默认 modules。",
                            },
                            {
                                "id": "frontend",
                                "label": "前端主导项目",
                                "impact": "写入 frontend preset 默认 modules。",
                            },
                        ],
                        "reply_format": "回复选项编号或 id",
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    assert main(["--source", str(source), "llm-usage", "--mode", "user-breakpoints", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "user-breakpoints"
    assert payload["format_version"] == 1
    assert payload["breakpoints"][0]["title"] == "选择 preset"
    assert payload["breakpoints"][0]["recommended"]["id"] == "fullstack"
    assert payload["breakpoints"][0]["options"][0]["impact"] == "写入 fullstack preset 默认 modules。"
    assert payload["breakpoints"][0]["reply_format"] == "回复选项编号或 id"


def test_llm_usage_json_format_is_limited_to_user_breakpoints(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"

    assert main(["--source", str(source), "llm-usage", "--mode", "auto-config", "--format", "json"]) == 1

    assert "LLM usage format not supported: mode=auto-config format=json" in capsys.readouterr().out


def test_llm_usage_mode_reports_missing_document(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    write(source / "docs" / "cli-usage-for-llm.md", "# Full usage\n")

    assert main(["--source", str(source), "llm-usage", "--mode", "auto-config"]) == 1

    assert "LLM usage document not found:" in capsys.readouterr().out


def test_init_interactive_reports_unavailable_stdin(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "source"
    create_copy_tree_source(source)

    def unavailable_stdin(_prompt: str) -> str:
        raise OSError("stdin unavailable")

    monkeypatch.setattr("builtins.input", unavailable_stdin)

    assert main(["--source", str(source), "init", str(tmp_path / "new"), "--interactive"]) == 1
    assert "interactive input unavailable" in capsys.readouterr().out


@pytest.mark.parametrize("exc", [EOFError("closed"), KeyboardInterrupt()])
def test_init_interactive_reports_cancelled_input(tmp_path: Path, monkeypatch, capsys, exc: BaseException) -> None:
    source = tmp_path / "source"
    target = tmp_path / "new"
    create_copy_tree_source(source)

    def cancelled_input(_prompt: str) -> str:
        raise exc

    monkeypatch.setattr("builtins.input", cancelled_input)

    assert main(["--source", str(source), "init", str(target), "--interactive"]) == 1
    assert "interactive input unavailable" in capsys.readouterr().out
    assert not (target / ".agentphilosophy.yaml").exists()


def test_prune_managed_deletes_only_stale_unchanged_managed_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "skills" / "skill-pack" / "SKILL.md").exists()

    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 0
    assert not (target / "skills" / "skill-pack" / "SKILL.md").exists()
    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "skills/skill-pack/SKILL.md" not in state_text


def test_prune_managed_refuses_manual_edits(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(target / "skills" / "skill-pack" / "SKILL.md", "# User edit\n")
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 1
    assert "refuse to prune changed managed file" in capsys.readouterr().out
    assert (target / "skills" / "skill-pack" / "SKILL.md").read_text(encoding="utf-8") == "# User edit\n"


def test_prune_managed_refuses_directory_replacing_managed_file(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    managed_file = target / "skills" / "skill-pack" / "SKILL.md"
    managed_file.unlink()
    managed_file.mkdir()
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 1
    assert "refuse to prune managed path that is not a regular file: skills/skill-pack/SKILL.md" in (
        capsys.readouterr().out
    )
    assert managed_file.is_dir()


def test_prune_managed_preserves_source_metadata_and_removes_empty_dirs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    state_before = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    old_source_hash = source_tree_hash(source)
    write(source / "modules" / "skill-pack" / "files" / "OTHER.md", "# Changed source\n")
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 0

    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert f"source_tree_hash: {old_source_hash}" in state_text
    assert f"source_tree_hash: {source_tree_hash(source)}" not in state_text
    assert "last_synced:" in state_text
    assert "skills/skill-pack/SKILL.md" in state_before
    assert "skills/skill-pack/SKILL.md" not in state_text
    assert not (target / "skills" / "skill-pack").exists()


def test_prune_managed_refuses_dry_run_apply_and_all_modes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules: []\nvars: {}\n",
        encoding="utf-8",
    )

    for extra_args in (["--dry-run"], ["--apply"], ["--all"]):
        assert main(["--source", str(source), "push", str(target), "--prune-managed", *extra_args]) == 1
        assert (target / "skills" / "skill-pack" / "SKILL.md").exists()


def test_prune_managed_refuses_invalid_target_config(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(
        source / "modules" / "requires-helper" / "module.yaml",
        """
name: requires-helper
description: Requires helper
version: 1.0.0
project_types: [fullstack]
requires: [helper]
conflicts: []
outputs:
  - id: marker
    type: rendered_file
    template: templates/marker.txt.j2
    target: marker.txt
    strategy: managed_replace
""".strip()
        + "\n",
    )
    write(source / "modules" / "requires-helper" / "templates" / "marker.txt.j2", "marker\n")
    write(
        source / "modules" / "helper" / "module.yaml",
        """
name: helper
description: Helper
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs: []
""".strip()
        + "\n",
    )
    write(
        source / "catalog.yaml",
        "schema_version: 1\n"
        "content_version: 0.2.0\n"
        "modules:\n"
        "  - name: skill-pack\n"
        "  - name: requires-helper\n"
        "  - name: helper\n",
    )
    create_target(target)
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules:\n  - requires-helper\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 1
    assert "requires disabled module" in capsys.readouterr().out
    assert (target / "skills" / "skill-pack" / "SKILL.md").exists()


def test_prune_managed_does_not_mask_active_output_source_drift(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(
        source / "modules" / "active" / "module.yaml",
        """
name: active
description: Active module
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
outputs:
  - id: active
    type: rendered_file
    template: templates/active.txt.j2
    target: active.txt
    strategy: managed_replace
""".strip()
        + "\n",
    )
    write(source / "modules" / "active" / "templates" / "active.txt.j2", "old\n")
    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: skill-pack\n  - name: active\n",
    )
    create_target(target, ["skill-pack", "active"])
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(source / "modules" / "active" / "templates" / "active.txt.j2", "new\n")
    (target / ".agentphilosophy.yaml").write_text(
        "project_name: Demo\nproject_type: fullstack\nmodules:\n  - active\nvars: {}\n",
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 0
    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    assert "source_tree_hash differs from current source" in capsys.readouterr().out


def test_migrate_write_config_promotes_draft_when_formal_config_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(target / "skills" / "skill-pack" / "SKILL.md", "# Legacy\n")

    assert main(["--source", str(source), "migrate", str(target), "--write-config"]) == 0

    assert (target / ".agentphilosophy.yaml").exists()
    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0


def test_migrate_inventory_includes_codex_project_skills(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    write(target / ".agents" / "skills" / "legacy-codex" / "SKILL.md", "# Legacy Codex Skill\n")

    assert main(["--source", str(source), "migrate", str(target)]) == 0

    inventory = (target / ".agents" / "migration" / "inventory.md").read_text(encoding="utf-8")
    assert "`.agents/skills/legacy-codex/SKILL.md`" in inventory


def test_migrate_write_config_refuses_to_replace_existing_config(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    create_copy_tree_source(source)
    create_target(target)
    original_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")

    assert main(["--source", str(source), "migrate", str(target), "--write-config"]) == 1

    assert (target / ".agentphilosophy.yaml").read_text(encoding="utf-8") == original_config
    assert (target / ".agents" / "migration" / "inventory.md").exists()
    assert (target / ".agents" / "migration" / "adopt-plan.yaml").exists()


def test_push_help_documents_safety_modes(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["push", "--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "preview without writing" in output
    assert "write rendered outputs" in output
    assert "prune stale managed files" in output


def test_source_tree_hash_excludes_registry_changes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    create_copy_tree_source(source)
    before = source_tree_hash(source)

    write(source / "registry.yaml", "projects: []\n")

    assert source_tree_hash(source) == before


def test_source_tree_hash_includes_llm_usage_json_docs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    create_copy_tree_source(source)
    write(
        source / "docs" / "llm-usage-user-breakpoints.json",
        '{"mode":"user-breakpoints","format_version":1,"breakpoints":[]}\n',
    )
    before = source_tree_hash(source)

    write(
        source / "docs" / "llm-usage-user-breakpoints.json",
        '{"mode":"user-breakpoints","format_version":1,"breakpoints":[{"id":"preset"}]}\n',
    )

    assert source_tree_hash(source) != before
