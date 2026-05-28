from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    }
    generated_docs = {
        path.name
        for path in (target / "aphilosophy").glob("*.md")
    }
    assert expected_docs <= generated_docs

    state = (target / ".agents" / "agentphilosophy-state.yaml").read_text(encoding="utf-8")
    for doc_name in expected_docs:
        assert f"aphilosophy/{doc_name}" in state


def test_packaged_fullstack_preset_renders_product_copy_standard(tmp_path: Path) -> None:
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

    product_copy_spec = target / "spec" / "ProductCopySpec.md"
    assert product_copy_spec.is_file()

    spec_text = product_copy_spec.read_text(encoding="utf-8")
    assert "用户可见文案不得解释内部实现细节" in spec_text
    assert "不得用文案区分产品 key 与上游或供应商 API key" in spec_text
    assert "客户服务端集成" in spec_text

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "用户可见文案不得解释内部实现、上游供应商或产品内部边界" in agents_text
    assert "SuperAgentAI API key" in agents_text


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
    assert "skill-portless-local-dev" in result.stdout
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
