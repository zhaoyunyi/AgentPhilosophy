from pathlib import Path

import pytest
import yaml

from agentphilosophy.cli import main

SOURCE = Path(__file__).resolve().parents[2]


def configure(target: Path, codex: str, repo: str = "skills") -> None:
    target.mkdir(exist_ok=True)
    (target / ".agentphilosophy.yaml").write_text(yaml.safe_dump({
        "project_name": "TargetCompatibility",
        "modules": ["skill-mattpocock-engineering"],
        "skill_targets": {"repo_skills": repo, "codex_project": codex},
        "vars": {"matt_implicit_skills": ["implement"]},
    }))


def run(*arguments: str) -> int:
    return main(["--source", str(SOURCE), *arguments])


@pytest.mark.parametrize("preset", ["orchestrator", "fullstack", "frontend", "mobile-sdk"])
@pytest.mark.parametrize("source", [SOURCE, SOURCE / "src/agentphilosophy/default_source"])
def test_user_gets_testing_skill_and_rules_from_each_default_preset(
    tmp_path: Path, source: Path, preset: str, validate_skill_contract
) -> None:
    """user Given 源码或包内预设，When 初始化并同步，Then 测试规范与完整双目标技能可用。"""
    assert main(["--source", str(source), "init", str(tmp_path), "--preset", preset]) == 0
    assert main(["--source", str(source), "push", str(tmp_path), "--apply"]) == 0
    assert (tmp_path / ".agents/skills/agentphilosophy-sync/SKILL.md").is_file()
    assert not (tmp_path / ".codex/skills").exists()
    skill = "test-suite-pruning"
    resources = ["SKILL.md", "references/decision-examples.md", "agents/openai.yaml", "assets/icon.svg"]
    for target in ("skills", ".agents/skills"):
        folder = tmp_path / target / skill
        validate_skill_contract(folder, skill)
        for resource in resources:
            assert (folder / resource).read_bytes() == (
                source / "modules/skill-test-suite-pruning" / skill / resource
            ).read_bytes()
        metadata = yaml.safe_load((folder / "agents/openai.yaml").read_text())
        assert metadata["policy"]["allow_implicit_invocation"] is True
        for icon in ("icon_small", "icon_large"):
            assert (folder / metadata["interface"][icon]).is_file()
    assert "测试套件治理" in (tmp_path / "spec/TestStrategy.md").read_text()
    assert "skills/test-suite-pruning/SKILL.md" in (tmp_path / "AGENTS.md").read_text()


def test_user_can_add_testing_skill_to_existing_project_without_changing_custom_paths(tmp_path: Path) -> None:
    """user Given 旧项目已选测试规范和自定义目录，When 追加技能并同步，Then 规范更新且定制保留。"""
    config_path = tmp_path / ".agentphilosophy.yaml"
    config = {
        "project_name": "ExistingTestingProject",
        "project_type": "fullstack",
        "modules": ["doc-templates", "spec-test-general"],
        "paths": {"spec_dir": "quality/spec"},
        "skill_targets": {"repo_skills": ".claude/skills", "codex_project": ".codex/skills"},
        "vars": {"test_command": "project-test"},
    }
    config_path.write_text(yaml.safe_dump(config))
    custom = tmp_path / ".agents/custom/AGENTS.custom.md"
    custom.parent.mkdir(parents=True)
    custom.write_text("## 项目自有验收\n保留真实支付验收。\n")
    assert run("push", str(tmp_path), "--apply") == 0
    assert "测试套件治理" in (tmp_path / "quality/spec/TestStrategy.md").read_text()
    assert "test-suite-pruning/SKILL.md" not in (tmp_path / "AGENTS.md").read_text()
    assert not (tmp_path / ".codex/skills/test-suite-pruning").exists()

    config["modules"].append("skill-test-suite-pruning")
    config_path.write_text(yaml.safe_dump(config))
    assert run("validate", str(tmp_path)) == 0
    assert run("push", str(tmp_path), "--dry-run") == 0
    assert not (tmp_path / ".codex/skills/test-suite-pruning").exists()
    assert run("push", str(tmp_path), "--apply") == 0
    agents = (tmp_path / "AGENTS.md").read_text()
    assert custom.read_text().strip() in agents
    assert "quality/spec/TestStrategy.md" in agents
    assert ".claude/skills/test-suite-pruning/SKILL.md" in agents
    assert "project-test" in (tmp_path / "quality/spec/TestStrategy.md").read_text()
    assert yaml.safe_load(config_path.read_text()) == config
    assert (tmp_path / ".claude/skills/test-suite-pruning/SKILL.md").read_bytes() == (
        tmp_path / ".codex/skills/test-suite-pruning/SKILL.md"
    ).read_bytes()
    assert run("status", "--project", str(tmp_path)) == 0


def test_user_keeps_local_testing_skill_when_sync_reports_unmanaged_conflict(tmp_path: Path, capsys) -> None:
    """user Given 已有同名自有技能，When 采用中央模块，Then 同步报告冲突且原文不被覆盖。"""
    config = {"project_name": "ExistingSkill", "modules": ["skill-test-suite-pruning"]}
    (tmp_path / ".agentphilosophy.yaml").write_text(yaml.safe_dump(config))
    skill = tmp_path / "skills/test-suite-pruning/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# 团队自有测试治理\n")
    assert run("push", str(tmp_path), "--apply") != 0
    assert "conflict" in capsys.readouterr().out.lower()
    assert skill.read_text() == "# 团队自有测试治理\n"


def test_explicit_legacy_target_migrates_with_resources_and_preserves_user_skills(tmp_path: Path) -> None:
    configure(tmp_path, ".codex/skills")
    assert run("push", str(tmp_path), "--apply") == 0
    legacy = tmp_path / ".codex/skills"
    expected = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
    custom = legacy / "user-owned/SKILL.md"
    custom.parent.mkdir()
    custom.write_text("# User-owned skill\n")

    configure(tmp_path, ".agents/skills")
    assert run("push", str(tmp_path), "--dry-run") == 0
    assert not (tmp_path / ".agents/skills").exists()
    assert run("push", str(tmp_path), "--apply") == 0
    for name, content in expected.items():
        assert (tmp_path / ".agents/skills" / name).read_bytes() == content
    assert run("push", str(tmp_path), "--prune-managed") == 0
    assert custom.read_text() == "# User-owned skill\n"
    assert not (legacy / "implement/SKILL.md").exists()
    policy = yaml.safe_load((tmp_path / ".agents/skills/implement/agents/openai.yaml").read_text())
    assert policy["policy"]["allow_implicit_invocation"] is True


def test_claude_skills_use_the_documented_repo_target(tmp_path: Path) -> None:
    configure(tmp_path, ".agents/skills", ".claude/skills")
    assert run("push", str(tmp_path), "--apply") == 0
    for relative in ("implement/SKILL.md", "tdd/mocking.md", "implement/agents/openai.yaml"):
        assert (tmp_path / ".claude/skills" / relative).read_bytes() == (
            tmp_path / ".agents/skills" / relative
        ).read_bytes()


def test_existing_implicit_legacy_directory_is_not_moved_by_an_upgrade(tmp_path: Path) -> None:
    configure(tmp_path, ".codex/skills")
    assert run("push", str(tmp_path), "--apply") == 0
    path = tmp_path / ".agentphilosophy.yaml"
    config = yaml.safe_load(path.read_text())
    del config["skill_targets"]["codex_project"]
    path.write_text(yaml.safe_dump(config))
    assert run("push", str(tmp_path), "--apply") == 0
    assert (tmp_path / ".codex/skills/implement/SKILL.md").exists()
    assert not (tmp_path / ".agents/skills").exists()
