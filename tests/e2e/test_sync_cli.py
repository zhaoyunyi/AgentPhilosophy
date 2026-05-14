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
    write(root / "catalog.yaml", "schema_version: 1\ncontent_version: 0.2.0\nmodules:\n  - name: doc-templates\n")
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


def test_cli_defaults_to_packaged_source_outside_central_repo(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "sync.py"),
            "init",
            str(target),
            "--preset",
            "fullstack",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    assert "- aphilosophy" in project_config


def test_cli_prints_llm_usage_document_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "sync.py"),
            "llm-usage",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "# AgentPhilosophy CLI 使用说明（给 LLM）" in result.stdout
    assert "skill-portless-local-dev" in result.stdout
    assert "aphilosophy" in result.stdout


def test_optional_portless_skill_renders_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: DemoProject
project_type: fullstack
modules:
  - skill-portless-local-dev
""".lstrip(),
    )

    commands = [
        ["validate", str(target)],
        ["push", str(target), "--dry-run"],
        ["push", str(target), "--apply"],
    ]
    for args in commands:
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parents[2] / "sync.py"),
                *args,
            ],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    repo_skill = target / "skills" / "portless-local-dev" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "portless-local-dev" / "SKILL.md"
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    assert "Portless 官方仓库" in repo_skill.read_text(encoding="utf-8")
