from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

from agentphilosophy.cli import main


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sandboxed_codex_command(script_path: Path) -> str:
    codex = script_path.parent / f"{script_path.stem}-codex" / "codex"
    write(
        codex,
        "#!/bin/sh\n"
        f"exec {shlex.quote(sys.executable)} {shlex.quote(str(script_path))} \"$@\"\n",
    )
    codex.chmod(0o755)
    os.environ["PATH"] = f"{codex.parent}{os.pathsep}{os.environ.get('PATH', '')}"
    return shlex.join(
        [
            "codex",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "workspace-write",
            "-",
        ]
    )


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


def test_bdd_default_harness_renders_release_notes_and_version_rules(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "release-managed-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    release_index = (target / "release-notes" / "README.md").read_text(encoding="utf-8")

    assert "- release-conventions" in project_config
    assert "MAJOR.MINOR.PATCH" in agents_text
    assert "release-notes/v<MAJOR>.<MINOR>.<PATCH>.md" in agents_text
    assert "发布回执" in agents_text
    assert "release-managed-project 发布说明索引" in release_index
    assert "兼容性与迁移" in release_index

    custom_index = target / ".agents" / "custom" / "release-notes" / "README.custom.md"
    write(custom_index, "- [v1.0.0](v1.0.0.md)：首次正式发布。\n")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert "[v1.0.0](v1.0.0.md)" in (target / "release-notes" / "README.md").read_text(encoding="utf-8")

    release_readme = target / "release-notes" / "README.md"
    release_readme.write_text(f"{release_readme.read_text(encoding='utf-8')}\n手工修改\n", encoding="utf-8")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1


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


def test_bdd_default_preset_excludes_optional_ponytail_and_superpowers(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "default-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    config_text = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "- model-constraints" in config_text
    assert "- skill-ponytail" not in config_text
    assert "- superpowers-system" not in config_text
    assert not (target / "skills" / "ponytail" / "SKILL.md").exists()
    assert not (target / ".codex" / "skills" / "ponytail" / "SKILL.md").exists()
    assert (target / "skills" / "portless-local-dev" / "PORTLESS-LICENSE.txt").is_file()
    assert (target / "skills" / "reverse-skill" / "REVERSE-SKILL-LICENSE.txt").is_file()
    assert (target / "skills" / "portless-local-dev" / "agents" / "openai.yaml").is_file()
    assert (target / "skills" / "reverse-skill" / "agents" / "openai.yaml").is_file()
    portless_text = (target / "skills" / "portless-local-dev" / "SKILL.md").read_text(encoding="utf-8")
    assert "dev.example.com" in portless_text
    assert "严格 OAuth" in portless_text
    assert "不能与 LAN 模式组合" in portless_text
    assert "选择合适的模型与推理强度" in agents_text
    assert "Superpowers System" not in agents_text


def test_bdd_default_preset_installs_complete_mattpocock_skill_family(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "complete-mattpocock-project"
    upstream_active_skills = {
        "ask-matt",
        "code-review",
        "codebase-design",
        "diagnosing-bugs",
        "domain-modeling",
        "grill-me",
        "grill-with-docs",
        "grilling",
        "handoff",
        "implement",
        "improve-codebase-architecture",
        "prototype",
        "research",
        "resolving-merge-conflicts",
        "setup-matt-pocock-skills",
        "tdd",
        "teach",
        "to-questionnaire",
        "to-spec",
        "to-tickets",
        "triage",
        "wait-what",
        "wayfinder",
        "wizard",
        "writing-for-agents",
    }
    compatibility_skills = {
        "writing-great-skills",
    }
    installed_skills = upstream_active_skills | compatibility_skills

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    repo_skills = {
        path.parent.name
        for path in (target / "skills").glob("*/SKILL.md")
        if path.parent.name in installed_skills
    }
    codex_skills = {
        path.parent.name
        for path in (target / ".codex" / "skills").glob("*/SKILL.md")
        if path.parent.name in installed_skills
    }
    assert repo_skills == installed_skills
    assert codex_skills == installed_skills
    for skill_name in installed_skills:
        assert (target / "skills" / skill_name / "agents" / "openai.yaml").is_file()
        assert (target / ".codex" / "skills" / skill_name / "agents" / "openai.yaml").is_file()
    for compatibility_name in ("to-prd", "to-issues"):
        repo_metadata = target / "skills" / compatibility_name / "agents" / "openai.yaml"
        codex_metadata = target / ".codex" / "skills" / compatibility_name / "agents" / "openai.yaml"
        assert "allow_implicit_invocation: false" in repo_metadata.read_text(encoding="utf-8")
        assert repo_metadata.read_bytes() == codex_metadata.read_bytes()

    assert (target / "skills" / "ask-matt" / "PHASE-BOUNDARIES.md").is_file()
    assert (target / "skills" / "wizard" / "template.sh").is_file()
    assert (target / "skills" / "writing-for-agents" / "SKILL-MECHANICS.md").is_file()

    prototype_text = (target / "skills" / "prototype" / "SKILL.md").read_text(encoding="utf-8")
    prototype_logic = (target / "skills" / "prototype" / "LOGIC.md").read_text(encoding="utf-8")
    prototype_ui = (target / "skills" / "prototype" / "UI.md").read_text(encoding="utf-8")
    assert "prototype/<name>" in prototype_text
    assert "自包含 HTML" in prototype_logic
    assert "guided walkthroughs" in prototype_logic
    assert "?variant=<name>" in prototype_ui
    assert "真实 header、sidebar、数据、权限" in prototype_ui

    wizard_template = (target / "skills" / "wizard" / "template.sh").read_text(encoding="utf-8")
    for helper in ("banner()", "pause()", "_existing()", "ask_secret()", "set_secret()", "set_var()"):
        assert helper in wizard_template
    assert "wslview" in wizard_template
    assert "TOTAL_MINUTES" not in wizard_template

    diagnosing_text = (target / "skills" / "diagnosing-bugs" / "SKILL.md").read_text(encoding="utf-8")
    assert "<REDACTED>" in diagnosing_text
    assert "环境变量" in diagnosing_text
    assert "建议用户后续单独运行" in diagnosing_text

    writing_metadata = (
        target / "skills" / "writing-for-agents" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" not in writing_metadata

    legacy_writing_text = (
        target / "skills" / "writing-great-skills" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "writing-for-agents" in legacy_writing_text
    legacy_writing_metadata = (
        target / "skills" / "writing-great-skills" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in legacy_writing_metadata

    grilling_text = (target / "skills" / "grilling" / "SKILL.md").read_text(encoding="utf-8")
    assert "每次只问一个问题" in grilling_text

    ask_matt_text = (target / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
    assert "新工具、新目录、新仓库或其他协作者" in ask_matt_text

    for active_skill in ("grill-with-docs", "domain-modeling", "implement", "code-review"):
        active_text = (target / "skills" / active_skill / "SKILL.md").read_text(encoding="utf-8")
        assert "PRD" not in active_text

    for configured_skill in ("triage", "wayfinder"):
        configured_text = (target / "skills" / configured_skill / "SKILL.md").read_text(encoding="utf-8")
        assert "停止，并请用户先运行 `/setup-matt-pocock-skills`" in configured_text


def test_bdd_default_preset_installs_code_review_graph_orchestration_skill(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "code-review-graph-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    config_text = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    assert "- skill-code-review-graph" in config_text

    for skill_root in (target / "skills", target / ".codex" / "skills"):
        skill_dir = skill_root / "code-review-graph"
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert (skill_dir / "CODE-REVIEW-GRAPH-LICENSE.txt").is_file()
        assert "MCP 是 agent 的主要查询接口" in skill_text
        assert "code-review-graph build" in skill_text
        assert "detect_changes_tool" in skill_text
        assert "图谱用于缩小读取范围，不能替代读取实现与测试" in skill_text


def test_bdd_complete_mattpocock_install_refuses_unmanaged_skill_conflict(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "mattpocock-conflict-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    unmanaged = target / "skills" / "ask-matt" / "SKILL.md"
    write(unmanaged, "# 用户自己的 ask-matt\n")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert unmanaged.read_text(encoding="utf-8") == "# 用户自己的 ask-matt\n"
    assert not (target / ".codex" / "skills" / "ask-matt" / "SKILL.md").exists()


def test_bdd_explicit_superpowers_selection_is_preserved(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "opt-in-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace("- model-constraints\n", "- model-constraints\n- superpowers-system\n", 1),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Superpowers System" in agents_text
    assert "Superpowers skill 版本为 `6.1.1`" in agents_text


def test_bdd_installed_optional_ponytail_and_superpowers_can_be_removed(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "remove-optional-skills"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace(
            "- model-constraints\n",
            "- model-constraints\n- skill-ponytail\n- superpowers-system\n",
            1,
        ),
        encoding="utf-8",
    )
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "skills" / "ponytail" / "SKILL.md").is_file()
    assert (target / ".codex" / "skills" / "ponytail" / "SKILL.md").is_file()
    assert (target / "skills" / "ponytail" / "PONYTAIL-LICENSE.txt").is_file()
    assert (target / "skills" / "ponytail" / "agents" / "openai.yaml").is_file()
    agents_path = target / "AGENTS.md"
    agents_before = agents_path.read_text(encoding="utf-8")
    assert "Superpowers System" in agents_before

    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        .replace("- skill-ponytail\n", "")
        .replace("- superpowers-system\n", ""),
        encoding="utf-8",
    )
    agents_path.write_text(f"{agents_before}\n手动修改\n", encoding="utf-8")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert (target / "skills" / "ponytail" / "SKILL.md").is_file()
    assert (target / ".codex" / "skills" / "ponytail" / "SKILL.md").is_file()

    agents_path.write_text(agents_before, encoding="utf-8")
    assert main(["--source", str(source), "push", str(target), "--dry-run"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert "Superpowers System" not in agents_path.read_text(encoding="utf-8")
    assert (target / "skills" / "ponytail" / "SKILL.md").is_file()
    assert (target / ".codex" / "skills" / "ponytail" / "SKILL.md").is_file()
    assert main(["--source", str(source), "push", str(target), "--prune-managed"]) == 0

    assert not (target / "skills" / "ponytail" / "SKILL.md").exists()
    assert not (target / ".codex" / "skills" / "ponytail" / "SKILL.md").exists()


def test_bdd_batch_apply_updates_versions_then_invokes_llm_for_documentation(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")

    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(
        source / "modules" / "doc-templates" / "templates" / "AGENTS.md.j2",
        "# {{ project_name }}\n\n新版协作规则\n",
    )
    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.3.0\nmodules:\n  - name: doc-templates\n",
    )
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
      - docs
""".lstrip(),
    )
    fake_llm = tmp_path / "fake_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

prompt = sys.stdin.read()
Path("docs").mkdir(exist_ok=True)
Path("docs/llm-prompt.md").write_text(prompt, encoding="utf-8")
agents = Path("AGENTS.md").read_text(encoding="utf-8")
with Path("README.md").open("a", encoding="utf-8") as stream:
    stream.write("\\n已根据新版规则更新：" + str("新版协作规则" in agents) + "\\n")
""".lstrip(),
    )

    command = sandboxed_codex_command(fake_llm)
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                command,
            ]
        )
        == 0
    )

    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    prompt = (target / "docs" / "llm-prompt.md").read_text(encoding="utf-8")
    assert "source_content_version: 0.3.0" in state_text
    assert "新版协作规则" in (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "已根据新版规则更新：True" in (target / "README.md").read_text(encoding="utf-8")
    assert "0.2.0 -> 0.3.0" in prompt
    assert "AGENTS.md" in prompt
    assert "README.md" in prompt
    assert "不要运行 Git 或 jj 命令" in prompt

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                command,
            ]
        )
        == 0
    )
    assert "documentation refresh skipped: project already current" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8").count("已根据新版规则更新") == 1

    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
      - CHANGELOG.md
      - docs
""".lstrip(),
    )
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                command,
            ]
        )
        == 0
    )
    assert (target / "README.md").read_text(encoding="utf-8").count("已根据新版规则更新") == 2
    state_text = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "- CHANGELOG.md" in state_text


def test_bdd_batch_documentation_update_rejects_unsandboxed_model_command(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    unsafe_llm = tmp_path / "unsafe_llm.py"
    write(
        unsafe_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
Path("README.md").write_text("unsafe\\n", encoding="utf-8")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join([sys.executable, str(unsafe_llm)]),
            ]
        )
        == 1
    )
    assert "must invoke the trusted PATH executable as 'codex'" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"

    expanded_command = shlex.split(sandboxed_codex_command(unsafe_llm))
    expanded_command[-1:-1] = ["--add-dir", str(tmp_path)]
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join(expanded_command),
            ]
        )
        == 1
    )
    assert "no extra writable roots" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"

    feature_command = shlex.split(sandboxed_codex_command(unsafe_llm))
    feature_command[-1:-1] = ["--enable", "unsafe-feature"]
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join(feature_command),
            ]
        )
        == 1
    )
    assert "unsupported or unsafe Codex arguments" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"

    executable_path_command = shlex.split(sandboxed_codex_command(unsafe_llm))
    executable_path_command[0] = str(shutil.which("codex"))
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join(executable_path_command),
            ]
        )
        == 1
    )
    assert "must invoke the trusted PATH executable as 'codex'" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"

    bypass_command = shlex.split(sandboxed_codex_command(unsafe_llm))
    bypass_command[-1:-1] = ["--sandbox", "danger-full-access"]
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join(bypass_command),
            ]
        )
        == 1
    )
    assert "requires exactly one workspace-write sandbox" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"

    attached_root_command = shlex.split(sandboxed_codex_command(unsafe_llm))
    attached_root_command[-1:-1] = [f"-C{tmp_path}"]
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                shlex.join(attached_root_command),
            ]
        )
        == 1
    )
    assert "no extra writable roots" in capsys.readouterr().out
    assert (target / "README.md").read_text(encoding="utf-8") == "# Dependent Project\n"


def test_bdd_batch_documentation_update_rejects_version_control_metadata_changes(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "BDD"], cwd=target, check=True)
    subprocess.run(["git", "config", "user.email", "bdd@example.test"], cwd=target, check=True)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=target, check=True, capture_output=True, text=True)
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "staging_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import subprocess
import sys

sys.stdin.read()
Path("README.md").write_text("staged by model\\n", encoding="utf-8")
subprocess.run(["git", "add", "README.md"], check=True)
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "LLM changed version-control metadata" in capsys.readouterr().out
    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "documentation_refresh:" not in state


def test_bdd_batch_documentation_update_rejects_git_hook_changes(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True, text=True)
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "git_hook_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
Path("README.md").write_text("documented\\n", encoding="utf-8")
Path(".git/hooks/pre-commit").write_text("#!/bin/sh\\nexit 1\\n", encoding="utf-8")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "LLM changed version-control metadata" in capsys.readouterr().out


def test_bdd_batch_documentation_update_rejects_jj_repository_config_changes(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(target / ".jj" / "repo" / "config.toml", "safe = true\n")
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "jj_config_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
Path("README.md").write_text("documented\\n", encoding="utf-8")
Path(".jj/repo/config.toml").write_text("tampered = true\\n", encoding="utf-8")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "LLM changed version-control metadata" in capsys.readouterr().out


def test_bdd_batch_documentation_update_rejects_git_worktree_pointer_changes(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(target / ".git", "gitdir: ../original-git-dir\n")
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "git_pointer_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
Path("README.md").write_text("documented\\n", encoding="utf-8")
Path(".git").write_text("gitdir: ../tampered-git-dir\\n", encoding="utf-8")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "LLM changed version-control metadata" in capsys.readouterr().out


def test_bdd_batch_documentation_update_fails_when_llm_changes_managed_file(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    write(target / ".gitignore", "ignored.txt\n")
    write(target / "ignored.txt", "safe\n")
    write(target / "mode.txt", "safe\n")
    write(target / ".jj" / "working_copy" / "checkout", "safe\n")
    write(target / ".jj" / "repo" / "config.toml", "safe = true\n")

    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.3.0\nmodules:\n  - name: doc-templates\n",
    )
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "unsafe_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import os
import sys

sys.stdin.read()
Path("AGENTS.md").write_text("# 被模型错误修改\\n", encoding="utf-8")
Path(".agents/agentphilosophy-state.yaml").write_text("tampered: true\\n", encoding="utf-8")
Path("src").mkdir(exist_ok=True)
Path("src/app.ts").write_text("export const tampered = true;\\n", encoding="utf-8")
Path("ignored.txt").write_text("tampered\\n", encoding="utf-8")
Path(".jj/working_copy/checkout").write_text("tampered\\n", encoding="utf-8")
Path(".jj/repo/config.toml").write_text("tampered = true\\n", encoding="utf-8")
Path("outside-link").symlink_to("README.md")
os.chmod("mode.txt", 0o755)
""".lstrip(),
    )

    command = sandboxed_codex_command(fake_llm)
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                command,
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "LLM changed managed files: AGENTS.md" in output
    assert "LLM changed protected files: .agents/agentphilosophy-state.yaml" in output
    assert "ignored.txt" in output
    assert "mode.txt" in output
    assert "outside-link" in output
    assert "src/app.ts" in output
    assert "LLM changed symlinks: outside-link" in output
    assert "LLM changed version-control metadata" in output
    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "documentation_refresh:" not in state


def test_bdd_batch_documentation_update_does_not_invoke_llm_after_sync_conflict(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(target / "AGENTS.md", "# 用户手工修改\n")
    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.3.0\nmodules:\n  - name: doc-templates\n",
    )
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "marker_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
with Path("README.md").open("a", encoding="utf-8") as stream:
    stream.write("\\n模型已调用\\n")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "模型已调用" not in (target / "README.md").read_text(encoding="utf-8")


def test_bdd_batch_documentation_update_rejects_symlink_created_in_allowed_directory(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    outside = tmp_path / "outside.txt"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    write(outside, "safe\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - docs
""".lstrip(),
    )
    fake_llm = tmp_path / "symlink_llm.py"
    write(
        fake_llm,
        f"""
from pathlib import Path
import sys

sys.stdin.read()
Path("docs").mkdir(exist_ok=True)
link = Path("docs/outside-link")
link.symlink_to({str(outside)!r})
link.write_text("tampered\\n", encoding="utf-8")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "LLM changed symlinks: docs/outside-link" in capsys.readouterr().out
    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "documentation_refresh:" not in state


def test_bdd_batch_documentation_update_reports_truncated_model_diagnostic(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "failing_llm.py"
    write(
        fake_llm,
        """
import sys

sys.stdin.read()
sys.stderr.write("discarded-prefix-" + "x" * 700 + " provider diagnostic: authentication denied")
raise SystemExit(7)
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "exit code 7" in output
    assert "provider diagnostic: authentication denied" in output
    assert "discarded-prefix" not in output
    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "documentation_refresh:" not in state


def test_bdd_batch_documentation_update_rejects_path_outside_project(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "dependent-project"
    seed_central_source(source)
    write(target / "README.md", "# Dependent Project\n")
    assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.3.0\nmodules:\n  - name: doc-templates\n",
    )
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - ../outside.md
""".lstrip(),
    )
    fake_llm = tmp_path / "marker_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
with Path("README.md").open("a", encoding="utf-8") as stream:
    stream.write("\\n模型已调用\\n")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "documentation path escapes project root" in capsys.readouterr().out
    assert "模型已调用" not in (target / "README.md").read_text(encoding="utf-8")

    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - docs/../.agents/custom
""".lstrip(),
    )
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "documentation path uses a protected project area" in capsys.readouterr().out
    assert "模型已调用" not in (target / "README.md").read_text(encoding="utf-8")

    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: DependentProject
    path: {target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 0
    )
    assert "模型已调用" in (target / "README.md").read_text(encoding="utf-8")
    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    assert "documentation_refresh:" in state


def test_bdd_batch_documentation_failure_does_not_block_later_project(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    invalid_target = tmp_path / "invalid-project"
    valid_target = tmp_path / "valid-project"
    seed_central_source(source)
    for target in (invalid_target, valid_target):
        write(target / "README.md", f"# {target.name}\n")
        assert main(["--source", str(source), "init", str(target), "--preset", "mobile-sdk"]) == 0
        assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    write(
        source / "catalog.yaml",
        "schema_version: 1\ncontent_version: 0.3.0\nmodules:\n  - name: doc-templates\n",
    )
    write(
        source / "registry.yaml",
        f"""
schema_version: 1
projects:
  - name: InvalidProject
    path: {invalid_target}
    documentation_paths:
      - ../outside.md
  - name: ValidProject
    path: {valid_target}
    documentation_paths:
      - README.md
""".lstrip(),
    )
    fake_llm = tmp_path / "fake_llm.py"
    write(
        fake_llm,
        """
from pathlib import Path
import sys

sys.stdin.read()
with Path("README.md").open("a", encoding="utf-8") as stream:
    stream.write("\\n文档更新完成\\n")
""".lstrip(),
    )

    assert (
        main(
            [
                "--source",
                str(source),
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                sandboxed_codex_command(fake_llm),
            ]
        )
        == 1
    )
    assert "文档更新完成" not in (invalid_target / "README.md").read_text(encoding="utf-8")
    assert "文档更新完成" in (valid_target / "README.md").read_text(encoding="utf-8")
