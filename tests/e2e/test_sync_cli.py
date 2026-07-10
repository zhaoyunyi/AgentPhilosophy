from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agentphilosophy import __version__


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
    assert "- skill-reverse-skill" in project_config
    assert "- skill-improve-codebase-architecture" in project_config
    assert "- skill-mattpocock-engineering" in project_config


def test_packaged_fullstack_preset_renders_all_aphilosophy_documents(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", "fullstack"],
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

    expected_docs = {
        "meta-decision-principles.md",
        "architecture-conflict-resolution.md",
        "governance-conflict-resolution.md",
        "cognitive-conflict-resolution.md",
        "authority-conflict-resolution.md",
        "operational-conflict-resolution.md",
        "security-conflict-resolution.md",
    }
    generated_docs = {
        path.name
        for path in (target / "aphilosophy").glob("*.md")
    }
    assert expected_docs <= generated_docs

    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    for doc_name in expected_docs:
        assert f"aphilosophy/{doc_name}" in state

    operational_text = (target / "aphilosophy" / "operational-conflict-resolution.md").read_text(encoding="utf-8")
    assert "运行态冲突解决协议" in operational_text
    assert "架构层独立性" in operational_text

    security_text = (target / "aphilosophy" / "security-conflict-resolution.md").read_text(encoding="utf-8")
    assert "安全对抗冲突解决协议" in security_text
    assert "欺骗性对齐检测" in security_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_renders_mattpocock_engineering_flow(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    expected_skills = [
        "grill-with-docs",
        "grilling",
        "domain-modeling",
        "to-spec",
        "to-tickets",
        "to-prd",
        "to-issues",
        "implement",
        "tdd",
        "code-review",
    ]
    for skill_name in expected_skills:
        repo_skill = target / "skills" / skill_name / "SKILL.md"
        codex_skill = target / ".codex" / "skills" / skill_name / "SKILL.md"
        assert repo_skill.is_file()
        assert codex_skill.is_file()
        assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")

    grill_text = (target / "skills" / "grill-with-docs" / "SKILL.md").read_text(encoding="utf-8")
    assert "/grill-with-docs" in grill_text
    assert "CONTEXT.md" in grill_text
    assert "ADR" in grill_text

    to_prd_text = (target / "skills" / "to-prd" / "SKILL.md").read_text(encoding="utf-8")
    assert "/to-prd" in to_prd_text
    assert "PRD" in to_prd_text

    to_issues_text = (target / "skills" / "to-issues" / "SKILL.md").read_text(encoding="utf-8")
    assert "/to-issues" in to_issues_text
    assert "vertical slice" in to_issues_text

    to_spec_text = (target / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
    assert "/to-spec" in to_spec_text
    assert "spec" in to_spec_text

    to_tickets_text = (target / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
    assert "/to-tickets" in to_tickets_text
    assert "tracer-bullet" in to_tickets_text

    implement_text = (target / "skills" / "implement" / "SKILL.md").read_text(encoding="utf-8")
    assert "/implement" in implement_text
    assert "/tdd" in implement_text
    assert "/code-review" in implement_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_renders_product_copy_standard(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    product_copy_spec = target / "spec" / "ProductCopySpec.md"
    assert product_copy_spec.is_file()

    spec_text = product_copy_spec.read_text(encoding="utf-8")
    assert "用户可见文案不得解释内部实现细节" in spec_text
    assert "不得用文案区分产品 key 与上游或供应商 API key" in spec_text
    assert "组织访问密钥用于服务端集成" in spec_text
    assert "Cadraq gateway key" not in spec_text
    assert "Customer gateway key" not in spec_text
    assert "SuperAgentAI" not in spec_text

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "用户可见文案不得解释内部实现、上游供应商或产品内部边界" in agents_text
    assert "组织访问密钥用于服务端集成" in agents_text
    assert "Cadraq gateway key" not in agents_text
    assert "Customer gateway key" not in agents_text
    assert "SuperAgentAI" not in agents_text

    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Codex CLI" not in claude_text
    assert "主要工具" not in claude_text
    assert "默认工具" not in claude_text
    assert "项目类型" not in claude_text
    assert "AgentPhilosophy 配置类型" in claude_text
    assert "不代表项目没有 UI、前端、产品体验或用户流程" in claude_text
    assert "遇到体验问题时，先定位相关代码、页面、截图、规格或用户流程" in claude_text
    assert "以其中的项目协作规范为准" in claude_text


def test_packaged_fullstack_without_optional_superpowers_has_no_blank_section(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    init_result = subprocess.run(
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
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    assert config_text.count("- superpowers-system\n") == 1
    config_path.write_text(config_text.replace("- superpowers-system\n", ""), encoding="utf-8")

    push_result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "sync.py"),
            "push",
            str(target),
            "--apply",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert push_result.returncode == 0, push_result.stderr + push_result.stdout

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "\n\n\n## 工程规范" not in agents_text


@pytest.mark.parametrize("preset", ["fullstack", "mobile-sdk", "orchestrator"])
def test_packaged_preset_renders_complete_ddd_standard(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    for args in (["init", str(target), "--preset", preset], ["push", str(target), "--apply"]):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[2] / "sync.py"), *args],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    ddd_text = (target / "spec" / "DDDSpec.md").read_text(encoding="utf-8")
    assert "# DDD 领域驱动设计规范" in ddd_text
    assert "通用语言（Ubiquitous Language）" in ddd_text
    assert "限界上下文（Bounded Context）" in ddd_text
    assert "聚合与充血模型（Aggregates & Rich Domain Model）" in ddd_text
    assert "明确契约和适合的 Context Map 模式" in ddd_text
    assert "ACL、OHS" in ddd_text
    assert "可选模式" in ddd_text
    assert "非领域代码不强制套用聚合" in ddd_text
    assert "English Instruction" not in ddd_text
    assert "This project strictly adheres to Domain-Driven Design" not in ddd_text
    assert "严禁进行技术性的“翻译”或抽象" not in ddd_text
    assert "必须通过防腐层（ACL）或开放主机服务（OHS）" not in ddd_text


def test_packaged_fullstack_renders_custom_aggregate_style(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    init_result = subprocess.run(
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
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    marker = "  primary_tool: Codex CLI\n"
    assert config_text.count(marker) == 1
    config_path.write_text(
        config_text.replace(marker, marker + "  aggregate_style: 事件溯源\n"),
        encoding="utf-8",
    )

    push_result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "sync.py"),
            "push",
            str(target),
            "--apply",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert push_result.returncode == 0, push_result.stderr + push_result.stdout

    ddd_text = (target / "spec" / "DDDSpec.md").read_text(encoding="utf-8")
    assert "项目聚合风格" in ddd_text
    assert "事件溯源" in ddd_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_declares_superpowers_version_by_default(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")

    assert "- superpowers-system" in project_config
    assert "Superpowers System" in agents_text
    assert "Superpowers skill 版本为 `6.1.1`" in agents_text
    assert "~/.codex/superpowers" in agents_text
    assert "~/.agents/skills/superpowers" in agents_text
    assert "superpowers-codex bootstrap" in agents_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_installs_ponytail_skill_by_default(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    repo_skill = target / "skills" / "ponytail" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "ponytail" / "SKILL.md"

    assert "- skill-ponytail" in project_config
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "Ponytail" in repo_skill_text
    assert "DietrichGebert/ponytail" in repo_skill_text
    assert "能不写就不写" in repo_skill_text
    assert "不要削减验证、错误处理、安全或可访问性" in repo_skill_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_installs_reverse_skill_by_default(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    repo_skill = target / "skills" / "reverse-skill" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "reverse-skill" / "SKILL.md"

    assert "- skill-reverse-skill" in project_config
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "reverse-skill" in repo_skill_text
    assert "zhaoxuya520/reverse-skill" in repo_skill_text
    assert "授权逆向、安全研究、CTF 或自有资产分析" in repo_skill_text
    assert "不要把上游仓库整包复制进目标项目" in repo_skill_text


@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_installs_portless_skill_by_default(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    commands = [
        ["init", str(target), "--preset", preset],
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

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    repo_skill = target / "skills" / "portless-local-dev" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "portless-local-dev" / "SKILL.md"

    assert "- skill-portless-local-dev" in project_config
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "Portless 官方仓库" in repo_skill_text
    assert "接入深度决策" in repo_skill_text
    assert "不要把 Portless 改造成唯一启动方式" in repo_skill_text


def test_cli_prints_llm_usage_document_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    sync_py = str(Path(__file__).resolve().parents[2] / "sync.py")

    result = subprocess.run(
        [
            sys.executable,
            sync_py,
            "llm-usage",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "# AgentPhilosophy CLI 使用说明（给 LLM）" in result.stdout
    assert "skill-ponytail" in result.stdout
    assert "skill-reverse-skill" in result.stdout
    assert "skill-portless-local-dev" in result.stdout
    assert "skill-philosophy-extraction" in result.stdout
    assert "skill-improve-codebase-architecture" in result.stdout
    assert "最低有效接入深度" in result.stdout
    assert "aphilosophy" in result.stdout
    assert "aphilosophy/cognitive-conflict-resolution.md" in result.stdout
    assert "aphilosophy/authority-conflict-resolution.md" in result.stdout

    auto_result = subprocess.run(
        [sys.executable, sync_py, "llm-usage", "--mode", "auto-config"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert auto_result.returncode == 0, auto_result.stderr + auto_result.stdout
    assert "# AgentPhilosophy 自动配置安装说明（给 LLM）" in auto_result.stdout
    assert "停止自动写入，返回用户断点" in auto_result.stdout
    assert "skill-ponytail" in auto_result.stdout
    assert "skill-reverse-skill" in auto_result.stdout
    assert "skill-philosophy-extraction" in auto_result.stdout
    assert "skill-improve-codebase-architecture" in auto_result.stdout

    breakpoint_result = subprocess.run(
        [sys.executable, sync_py, "llm-usage", "--mode", "user-breakpoints"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert breakpoint_result.returncode == 0, breakpoint_result.stderr + breakpoint_result.stdout
    assert "# AgentPhilosophy 用户断点配置说明（给 LLM）" in breakpoint_result.stdout
    assert "reply_format: 回复选项编号或 id" in breakpoint_result.stdout
    assert "skill-ponytail" in breakpoint_result.stdout
    assert "skill-reverse-skill" in breakpoint_result.stdout
    assert "skill-philosophy-extraction" in breakpoint_result.stdout
    assert "skill-improve-codebase-architecture" in breakpoint_result.stdout

    breakpoint_json_result = subprocess.run(
        [sys.executable, sync_py, "llm-usage", "--mode", "user-breakpoints", "--format", "json"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert breakpoint_json_result.returncode == 0, breakpoint_json_result.stderr + breakpoint_json_result.stdout
    breakpoint_payload = json.loads(breakpoint_json_result.stdout)
    assert breakpoint_payload["mode"] == "user-breakpoints"
    assert breakpoint_payload["format_version"] == 1
    assert breakpoint_payload["breakpoints"][0]["title"] == "选择接入路径"
    assert breakpoint_payload["breakpoints"][0]["recommended"]["id"] == "migrate"
    assert breakpoint_payload["breakpoints"][0]["options"][0]["id"] == "migrate"
    assert breakpoint_payload["breakpoints"][0]["reply_format"] == "回复选项编号或 id"


def test_readme_documents_current_stable_release_install_command() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")

    assert f"AgentPhilosophy.git@v{__version__}" in readme


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
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "Portless 官方仓库" in repo_skill_text
    assert "接入深度决策" in repo_skill_text
    assert "一次性 `portless run`，不改文件" in repo_skill_text


def test_optional_philosophy_extraction_skill_renders_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: DemoProject
project_type: orchestrator
modules:
  - aphilosophy
  - skill-philosophy-extraction
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

    repo_skill = target / "skills" / "philosophy-extraction" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "philosophy-extraction" / "SKILL.md"
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert (target / "aphilosophy" / "meta-decision-principles.md").is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "Philosophy Extraction Skill" in repo_skill_text
    assert "脱水" in repo_skill_text
    assert "不要直接改托管的 `aphilosophy/`" in repo_skill_text
    assert "modules/aphilosophy/templates/{domain}-conflict-resolution.md.j2" in repo_skill_text


def test_optional_improve_codebase_architecture_skill_renders_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: DemoProject
project_type: fullstack
modules:
  - skill-improve-codebase-architecture
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

    repo_skill = target / "skills" / "improve-codebase-architecture" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "improve-codebase-architecture" / "SKILL.md"
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "Improve Codebase Architecture" in repo_skill_text
    assert "AgentPhilosophy ArchitectureSpec" in repo_skill_text
    assert "architecture-review-" in repo_skill_text
    assert "你想先深入哪一个候选？" in repo_skill_text


def test_optional_code_review_skill_renders_from_default_source(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    target = tmp_path / "target"
    write(
        target / ".agentphilosophy.yaml",
        """
project_name: DemoProject
project_type: fullstack
modules:
  - skill-code-review
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

    repo_skill = target / "skills" / "code-review" / "SKILL.md"
    codex_skill = target / ".codex" / "skills" / "code-review" / "SKILL.md"
    assert repo_skill.is_file()
    assert codex_skill.is_file()
    assert repo_skill.read_text(encoding="utf-8") == codex_skill.read_text(encoding="utf-8")
    repo_skill_text = repo_skill.read_text(encoding="utf-8")
    assert "name: code-review" in repo_skill_text
    assert "/code-review" in repo_skill_text
    assert "Standards" in repo_skill_text
    assert "Spec" in repo_skill_text


def test_packaged_orchestrator_adopts_matching_verification_guide_output(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    sync_py = str(Path(__file__).resolve().parents[2] / "sync.py")

    for args in (["init", str(target), "--preset", "orchestrator"], ["push", str(target), "--apply"]):
        result = subprocess.run(
            [sys.executable, sync_py, *args],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    strategy_path = target / "spec" / "TestStrategy.md"
    baseline = strategy_path.read_text(encoding="utf-8")
    assert "## 验证边界" not in baseline
    strategy_path.write_text(
        baseline
        + "\n## 验证边界\n\n"
        + "具体到 change class 的必跑命令、smoke 选择、未覆盖边界记录和禁止事项见 "
        + "`docs/guides/verification-boundaries.md`。完成前必须使用当前命令输出作为证据，"
        + "不能用旧日志或推测替代。\n",
        encoding="utf-8",
    )

    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    marker = "  primary_tool: Codex CLI\n"
    assert config_text.count(marker) == 1
    config_path.write_text(
        config_text.replace(
            marker,
            marker + "  verification_guide_path: docs/guides/verification-boundaries.md\n",
        ),
        encoding="utf-8",
    )

    apply_result = subprocess.run(
        [sys.executable, sync_py, "push", str(target), "--apply"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert apply_result.returncode == 0, apply_result.stderr + apply_result.stdout
    assert "skip: spec/TestStrategy.md (already up to date)" in apply_result.stdout
    assert "conflict: spec/TestStrategy.md" not in apply_result.stdout

    second_dry_run = subprocess.run(
        [sys.executable, sync_py, "push", str(target), "--dry-run"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second_dry_run.returncode == 0, second_dry_run.stderr + second_dry_run.stdout
    assert "conflict: spec/TestStrategy.md" not in second_dry_run.stdout
