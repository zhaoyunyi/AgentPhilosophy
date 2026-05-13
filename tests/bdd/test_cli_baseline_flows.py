from __future__ import annotations

from pathlib import Path
from shutil import copytree

import yaml

from agentphilosophy.cli import main

TEST_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "cli-baseline"
BASELINE_ROOT = TEST_ROOT / "baselines" / "cli-baseline"


def copy_fixture(name: str, destination: Path) -> Path:
    source = FIXTURE_ROOT / name
    assert source.exists(), f"missing fixture: {source}"
    copytree(source, destination)
    return destination


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def assert_files_match_baseline(
    project_root: Path,
    baseline_name: str,
    *,
    allowed_extra_files: set[str] | None = None,
) -> None:
    baseline = BASELINE_ROOT / baseline_name
    assert baseline.exists(), f"missing baseline: {baseline}"
    baseline_files = {
        path.relative_to(baseline).as_posix()
        for path in baseline.rglob("*")
        if path.is_file()
    }
    project_files = {
        path.relative_to(project_root).as_posix()
        for path in project_root.rglob("*")
        if path.is_file()
    }
    assert baseline_files - project_files == set()
    assert project_files - baseline_files == (allowed_extra_files or set())
    for expected in sorted(path for path in baseline.rglob("*") if path.is_file()):
        relative = expected.relative_to(baseline)
        actual = project_root / relative
        assert actual.exists(), f"missing generated file: {relative.as_posix()}"
        assert actual.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8")


def managed_state_paths(project_root: Path) -> list[str]:
    state = yaml.safe_load((project_root / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8"))
    return sorted(str(item["path"]) for item in state["files"])


def assert_report_has_no_warnings(output: str) -> None:
    assert "[warning]" not in output
    assert "[error]" not in output


def test_bdd_new_project_cli_generation_matches_golden_baseline(tmp_path: Path, capsys) -> None:
    source = copy_fixture("central-source", tmp_path / "source")
    target = tmp_path / "product-app"

    assert main(["--source", str(source), "init", str(target), "--preset", "fullstack"]) == 0
    assert main(["--source", str(source), "validate", str(target)]) == 0

    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".agents" / "agentphilosophy-state.yaml").exists()

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert_files_match_baseline(
        target,
        "new-project",
        allowed_extra_files={".agents/agentphilosophy-state.yaml"},
    )
    assert managed_state_paths(target) == [
        "AGENTS.md",
        "CLAUDE.md",
        "skills/repo-management/SKILL.md",
        "spec/BDDSpec.md",
    ]
    capsys.readouterr()
    assert main(["--source", str(source), "status", "--project", str(target)]) == 0
    status_output = capsys.readouterr().out
    assert f"[info] status checked: {target}" in status_output
    assert_report_has_no_warnings(status_output)


def test_bdd_legacy_project_migration_adoption_and_conflict_baseline(tmp_path: Path, capsys) -> None:
    source = copy_fixture("central-source", tmp_path / "source")
    target = tmp_path / "legacy-app"
    write(target / "AGENTS.md", "# Legacy App\n\n旧项目规则\n")
    write(target / "skills" / "repo-management" / "SKILL.md", "# Legacy Repo Skill\n")

    assert main(["--source", str(source), "migrate", str(target), "--write-config"]) == 0
    assert_files_match_baseline(
        target,
        "legacy-after-write-config",
        allowed_extra_files={"AGENTS.md", "skills/repo-management/SKILL.md"},
    )

    capsys.readouterr()
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    unmanaged_conflict_output = capsys.readouterr().out
    assert "conflict: AGENTS.md" in unmanaged_conflict_output
    assert "conflict: skills/repo-management/SKILL.md" in unmanaged_conflict_output
    assert (target / ".agents" / "migration" / "diffs" / "AGENTS.md.new").read_text(
        encoding="utf-8"
    ) == (BASELINE_ROOT / "legacy-after-write-config" / ".agents" / "migration" / "diffs" / "AGENTS.md.new").read_text(
        encoding="utf-8"
    )
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Legacy App\n\n旧项目规则\n"

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
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert_files_match_baseline(
        target,
        "legacy-after-adopt-apply",
        allowed_extra_files={
            ".agents/agentphilosophy-state.yaml",
            ".agents/migration/adopt-plan.yaml",
            ".agents/migration/diffs/AGENTS.md.diff",
            ".agents/migration/diffs/AGENTS.md.new",
            ".agents/migration/diffs/CLAUDE.md.new",
            ".agents/migration/diffs/skills__repo-management__SKILL.md.diff",
            ".agents/migration/diffs/skills__repo-management__SKILL.md.new",
            ".agents/migration/diffs/spec__BDDSpec.md.new",
            ".agents/migration/inventory.md",
            ".agents/migration/proposed.agentphilosophy.yaml",
        },
    )

    write(target / "AGENTS.md", "# legacy-app\n\n手动追加\n")
    capsys.readouterr()
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    manual_conflict_output = capsys.readouterr().out
    assert "conflict: AGENTS.md" in manual_conflict_output
    assert "managed file was changed manually" in manual_conflict_output
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# legacy-app\n\n手动追加\n"


def test_bdd_prune_managed_removes_only_stale_unchanged_outputs(tmp_path: Path) -> None:
    source = copy_fixture("central-source", tmp_path / "source")
    target = tmp_path / "product-app"

    assert main(["--source", str(source), "init", str(target), "--preset", "fullstack"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "skills" / "repo-management" / "SKILL.md").exists()

    config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    (target / ".agentphilosophy.yaml").write_text(
        config.replace("- skill-repo-management\n", ""),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 0
    assert not (target / "skills" / "repo-management" / "SKILL.md").exists()
    assert not (target / "skills" / "repo-management").exists()
    assert_files_match_baseline(
        target,
        "pruned-project",
        allowed_extra_files={".agents/agentphilosophy-state.yaml"},
    )
    assert managed_state_paths(target) == [
        "AGENTS.md",
        "CLAUDE.md",
        "spec/BDDSpec.md",
    ]


def test_bdd_registry_batch_dry_run_and_apply_use_declared_projects(tmp_path: Path, capsys) -> None:
    source = copy_fixture("central-source", tmp_path / "source")
    product = tmp_path / "product-app"
    admin = tmp_path / "admin-app"

    assert main(["--source", str(source), "init", str(product), "--preset", "fullstack"]) == 0
    assert main(["--source", str(source), "init", str(admin), "--preset", "fullstack"]) == 0
    write(
        source / "registry.yaml",
        yaml.safe_dump(
            {
                "schema_version": 1,
                "projects": [
                    {"name": "product", "path": str(product)},
                    {"name": "admin", "path": str(admin)},
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
    )

    capsys.readouterr()
    assert main(["--source", str(source), "status"]) == 0
    registry_status_output = capsys.readouterr().out
    assert "[info] product: reachable" in registry_status_output
    assert "[info] admin: reachable" in registry_status_output
    assert_report_has_no_warnings(registry_status_output)

    capsys.readouterr()
    assert main(["--source", str(source), "push", "--all", "--dry-run"]) == 0
    registry_dry_run_output = capsys.readouterr().out
    assert "[info] product: add: AGENTS.md" in registry_dry_run_output
    assert "[info] admin: add: AGENTS.md" in registry_dry_run_output
    assert_report_has_no_warnings(registry_dry_run_output)
    assert not (product / "AGENTS.md").exists()
    assert not (admin / "AGENTS.md").exists()

    assert main(["--source", str(source), "push", "--all", "--apply"]) == 0
    assert_files_match_baseline(
        product,
        "new-project",
        allowed_extra_files={".agents/agentphilosophy-state.yaml"},
    )
    assert managed_state_paths(product) == [
        "AGENTS.md",
        "CLAUDE.md",
        "skills/repo-management/SKILL.md",
        "spec/BDDSpec.md",
    ]
    assert_files_match_baseline(
        admin,
        "admin-project",
        allowed_extra_files={".agents/agentphilosophy-state.yaml"},
    )
    assert managed_state_paths(admin) == [
        "AGENTS.md",
        "CLAUDE.md",
        "skills/repo-management/SKILL.md",
        "spec/BDDSpec.md",
    ]
