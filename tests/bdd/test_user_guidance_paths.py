import json
import re
from pathlib import Path

import pytest
import yaml

from agentphilosophy.cli import main

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("source", [ROOT, ROOT / "src/agentphilosophy/default_source"])
def test_user_gets_target_options_matching_installed_outputs(source: Path, tmp_path: Path, capsys) -> None:
    """user Given 新项目，When 读取 JSON 向导再安装，Then 推荐路径对应真实输出。"""
    assert main(["--source", str(source), "llm-usage", "--mode", "user-breakpoints", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    targets = next(item for item in payload["breakpoints"] if item["id"] == "skill-targets")
    options = {item["id"]: item for item in targets["options"]}
    recommended = options[targets["recommended"]["id"]]

    project = tmp_path / "project"
    assert main(["--source", str(source), "init", str(project), "--preset", "orchestrator"]) == 0
    config_path = project / ".agentphilosophy.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["modules"] = ["skill-loop-check"]
    config["skill_targets"]["claude_project"] = ".claude/skills"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True))
    assert main(["--source", str(source), "push", str(project), "--apply"]) == 0
    expected = {config["skill_targets"][key] for key in ("repo_skills", "codex_project")}
    advertised = {path.rstrip("/") for path in re.findall(r"`([^`]+)`", recommended["label"])}
    assert advertised == expected
    for path in expected:
        assert (project / path / "loop-check/SKILL.md").is_file()
    # 设置保留字段不会凭空产生第三路，条件选项必须向用户说明所需能力。
    assert not (project / ".claude/skills").exists()
    for option_id in ("repo-only", "repo-codex-claude"):
        assert "自定义模块" in options[option_id]["label"] + options[option_id]["impact"]


@pytest.mark.parametrize("custom_dir", [".agents/custom", "project-rules/local"])
def test_user_reads_loop_plan_from_their_configured_custom_directory(tmp_path: Path, custom_dir: str) -> None:
    """user Given 自定义规则目录和既有计划，When 同步技能，Then 指向原计划且不另建默认计划。"""
    project = tmp_path / "project"
    project.mkdir()
    plan = project / custom_dir / "loop-check.md"
    plan.parent.mkdir(parents=True)
    original = "# 自有巡检计划\n\n范围：本仓文档；排除发布与部署。\n"
    plan.write_text(original)
    (project / ".agentphilosophy.yaml").write_text(yaml.safe_dump({
        "project_name": "Project", "project_type": "orchestrator",
        "modules": ["skill-loop-check"], "paths": {"custom_dir": custom_dir},
    }))
    for _ in range(2):
        assert main(["--source", str(ROOT), "push", str(project), "--apply"]) == 0
    for prefix in ("skills", ".agents/skills"):
        skill = (project / prefix / "loop-check/SKILL.md").read_text()
        assert f"`{custom_dir}/loop-check.md`" in skill
        if custom_dir != ".agents/custom":
            assert "`.agents/custom/loop-check.md`" not in skill
    assert plan.read_text() == original
    if custom_dir != ".agents/custom":
        assert not (project / ".agents/custom/loop-check.md").exists()
