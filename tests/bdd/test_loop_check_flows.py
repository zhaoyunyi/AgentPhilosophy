from pathlib import Path

import pytest
import yaml

from agentphilosophy.cli import main

SOURCE = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("preset", ["orchestrator", "fullstack", "frontend", "mobile-sdk"])
def test_user_installs_loop_check_with_complete_resources(
    tmp_path: Path, preset: str, validate_skill_contract
) -> None:
    """user Given 新仓库，When 同步默认方案，Then 两个入口可读取完整巡检技能。"""
    target = tmp_path / preset
    assert main(["--source", str(SOURCE), "init", str(target), "--preset", preset]) == 0
    assert main(["--source", str(SOURCE), "push", str(target), "--apply"]) == 0

    repo_skill = target / "skills/loop-check"
    host_skill = target / ".agents/skills/loop-check"
    for folder in (repo_skill, host_skill):
        validate_skill_contract(folder, "loop-check")
        metadata = yaml.safe_load((folder / "agents/openai.yaml").read_text())
        assert metadata["policy"]["allow_implicit_invocation"] is True
        for reference in ("references/checks.md", "references/plan.md"):
            assert (folder / reference).is_file()
            assert reference in (folder / "SKILL.md").read_text()
    repo_files = {p.relative_to(repo_skill): p.read_bytes() for p in repo_skill.rglob("*") if p.is_file()}
    host_files = {p.relative_to(host_skill): p.read_bytes() for p in host_skill.rglob("*") if p.is_file()}
    assert repo_files == host_files
    # 安装技能不冒充仓库事实，也不自动创建计划、退役记录或定时任务。
    assert not (target / ".agents/custom/loop-check.md").exists()
    assert not (target / "docs/retirements.md").exists()


def test_user_keeps_repository_check_plan_when_resyncing(tmp_path: Path) -> None:
    """user Given 自有巡检计划，When 重新同步技能，Then 计划和排除项保持原样。"""
    target = tmp_path / "project"
    assert main(["--source", str(SOURCE), "init", str(target), "--preset", "orchestrator"]) == 0
    plan = target / ".agents/custom/loop-check.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    original = "# 本仓巡检\n\n范围：src/、tests/；排除生产数据和正在运行的工作区。\n"
    plan.write_text(original)
    for _ in range(2):
        assert main(["--source", str(SOURCE), "push", str(target), "--apply"]) == 0
    assert (target / ".agents/skills/loop-check/SKILL.md").is_file()
    assert plan.read_text() == original


def test_user_keeps_unmanaged_loop_check_on_install_conflict(tmp_path: Path) -> None:
    """user Given 同名自有技能，When 安装巡检模块，Then 报冲突并保留自有内容。"""
    target = tmp_path / "project"
    assert main(["--source", str(SOURCE), "init", str(target), "--preset", "orchestrator"]) == 0
    unmanaged = target / "skills/loop-check/SKILL.md"
    unmanaged.parent.mkdir(parents=True)
    original = "# 用户自己的巡检实现\n"
    unmanaged.write_text(original)
    assert main(["--source", str(SOURCE), "push", str(target), "--apply"]) == 1
    assert unmanaged.read_text() == original
    assert not (target / ".agents/skills/loop-check/SKILL.md").exists()
