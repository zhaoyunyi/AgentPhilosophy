from pathlib import Path

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


def test_new_projects_discover_skills_in_agents_directory(tmp_path: Path) -> None:
    assert run("init", str(tmp_path), "--preset", "orchestrator") == 0
    assert run("push", str(tmp_path), "--apply") == 0
    assert (tmp_path / ".agents/skills/agentphilosophy-sync/SKILL.md").is_file()
    assert not (tmp_path / ".codex/skills").exists()


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
