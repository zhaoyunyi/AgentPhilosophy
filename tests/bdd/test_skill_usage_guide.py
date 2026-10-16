import json
from pathlib import Path

import pytest
import yaml

from agentphilosophy.cli import main
from agentphilosophy.rendering import render_outputs
from agentphilosophy.source import load_modules

ROOT = Path(__file__).resolve().parents[2]


def guide_rows(text: str) -> dict[tuple[str, str], list[str]]:
    rows = {}
    for line in text.splitlines():
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) != 5 or not cells[0].startswith("`$"):
            continue
        name = cells[0].strip("`").removeprefix("$")
        module = cells[1].strip("`")
        key = name, module
        assert key not in rows, key
        rows[key] = cells
    return rows


@pytest.mark.parametrize("source", [ROOT, ROOT / "src/agentphilosophy/default_source"])
def test_user_can_find_every_distributed_skill_and_its_invocation_policy(source: Path, tmp_path: Path, capsys) -> None:
    """user Given 当前内容源，When 请求完整用法，Then 每个可安装技能均有正确模块、调用策略和示例。"""
    assert main(["--source", str(source), "llm-usage"]) == 0
    rows = guide_rows(capsys.readouterr().out)
    expected = set()
    for name, module in load_modules(source).items():
        if not any(str(capability).startswith("skill:") for capability in module.data.get("provides", [])):
            continue
        config = {"project_name": "Demo", "project_type": "fullstack", "modules": [name]}
        outputs = render_outputs(source, tmp_path, config, [module])
        files = {output.rel_path: output.content for output in outputs if output.rel_path.startswith("skills/")}
        for path, content in files.items():
            if not path.endswith("/SKILL.md"):
                continue
            metadata = yaml.safe_load(content.decode().split("---", 2)[1])
            key = metadata["name"], name
            expected.add(key)
            assert key in rows, f"用法缺少可安装技能：{key}"
            row = rows[key]
            policy = yaml.safe_load(files.get(path.removesuffix("SKILL.md") + "agents/openai.yaml", b"{}"))
            explicit = metadata.get("disable-model-invocation") or policy.get("policy", {}).get(
                "allow_implicit_invocation"
            ) is False
            assert ("显式" if explicit else "自动") in row[2], key
            assert row[3], key
            assert f"${metadata['name']} " in row[4], key
    assert set(rows) == expected


@pytest.mark.parametrize("mode", ["auto-config", "user-breakpoints"])
def test_user_can_reach_complete_skill_guide_from_each_short_mode(mode: str, capsys) -> None:
    """user Given 精简配置入口，When 需要选择未单独提问的技能，Then 能取得同源完整指南。"""
    assert main(["--source", str(ROOT), "llm-usage", "--mode", mode]) == 0
    output = capsys.readouterr().out
    assert "agentphilosophy-sync llm-usage" in output
    assert "cli/skills.md" in output
    for module in ("skill-loop-check", "skill-restate-goal", "skill-ui-ux-loop", "skill-orchestrate-grok-cli"):
        assert module in output


def test_user_can_follow_json_guide_command_and_install_an_optional_skill(tmp_path: Path, capsys) -> None:
    """user Given JSON 向导与已接入项目，When 按模块映射追加技能，Then 新技能可用且旧配置和计划保留。"""
    original_prefix = ["--source", str(ROOT)]
    assert main([*original_prefix, "llm-usage", "--mode", "user-breakpoints", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    guide = payload["skill_guide"]
    assert guide["command"] == "agentphilosophy-sync llm-usage"
    assert guide["arguments"] == ["llm-usage"]
    assert main([*original_prefix, *guide["arguments"]]) == 0
    rows = guide_rows(capsys.readouterr().out)
    skill = "restate-goal"
    module = next(module for name, module in rows if name == skill)
    target = tmp_path / "project"
    assert main(["--source", str(ROOT), "init", str(target), "--preset", "fullstack"]) == 0
    assert main(["--source", str(ROOT), "push", str(target), "--apply"]) == 0
    assert not (target / ".agents/skills" / skill).exists()
    config_path = target / ".agentphilosophy.yaml"
    config = yaml.safe_load(config_path.read_text())
    existing_modules = list(config["modules"])
    plan = target / ".agents/custom/loop-check.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# 用户巡检计划\n")
    config["modules"].append(module)
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    assert main(["--source", str(ROOT), "validate", str(target)]) == 0
    assert main(["--source", str(ROOT), "push", str(target), "--dry-run"]) == 0
    assert main(["--source", str(ROOT), "push", str(target), "--apply"]) == 0
    assert main(["--source", str(ROOT), "status", "--project", str(target)]) == 0
    assert (target / ".agents/skills" / skill / "SKILL.md").read_bytes() == (
        target / "skills" / skill / "SKILL.md"
    ).read_bytes()
    assert set(existing_modules) <= set(yaml.safe_load(config_path.read_text())["modules"])
    assert plan.read_text() == "# 用户巡检计划\n"


def test_user_keeps_selected_source_when_navigating_outside_a_central_checkout(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """user Given 业务目录中的自定义源调用，When 按 JSON 导航，Then 仍读取该源而非安装包。"""
    source = tmp_path / "selected-source"
    docs = source / "docs"
    docs.mkdir(parents=True)
    marker = "# 团队自有内容源的技能指南\n"
    (docs / "cli-usage-for-llm.md").write_text(marker)
    (docs / "llm-usage-user-breakpoints.json").write_bytes(
        (ROOT / "docs/llm-usage-user-breakpoints.json").read_bytes()
    )
    business_repo = tmp_path / "business"
    business_repo.mkdir()
    monkeypatch.chdir(business_repo)
    original_prefix = ["--source", str(source)]
    assert main([*original_prefix, "llm-usage", "--mode", "user-breakpoints", "--format", "json"]) == 0
    guide = json.loads(capsys.readouterr().out)["skill_guide"]
    assert guide["preserve_invocation"] is True
    assert main([*original_prefix, *guide["arguments"]]) == 0
    assert capsys.readouterr().out == marker


@pytest.mark.parametrize("preset", ["orchestrator", "fullstack", "frontend", "mobile-sdk"])
def test_user_sees_the_same_default_skill_modules_in_guide_and_new_project(
    preset: str, tmp_path: Path, capsys
) -> None:
    """user Given 一个预设，When 按用法选择新项目配置，Then 默认安装范围与实际 init 一致。"""
    assert main(["--source", str(ROOT), "llm-usage"]) == 0
    guide = capsys.readouterr().out
    skill_modules = {module for _, module in guide_rows(guide)}
    advertised = set()
    listed = set()
    for line in guide.splitlines():
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) != 3 or cells[0].strip("`") not in skill_modules:
            continue
        module = cells[0].strip("`")
        assert module not in listed
        listed.add(module)
        if cells[1] == "全部四类" or preset in cells[1]:
            advertised.add(module)
    assert listed == skill_modules
    target = tmp_path / "project"
    assert main(["--source", str(ROOT), "init", str(target), "--preset", preset]) == 0
    installed = yaml.safe_load((target / ".agentphilosophy.yaml").read_text())["modules"]
    assert advertised == set(installed) & skill_modules
