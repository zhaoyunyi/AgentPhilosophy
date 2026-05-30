from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


def load_generator():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "generate-release-notes.py"
    spec = importlib.util.spec_from_file_location("generate_release_notes", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_generate_release_notes_summarizes_diff_commits_and_module_versions(tmp_path: Path) -> None:
    generator = load_generator()
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")

    write(repo / "pyproject.toml", '[project]\nname = "agentphilosophy"\nversion = "0.4.4"\n')
    write(repo / "catalog.yaml", "schema_version: 1\ncontent_version: 0.4.4\nmodules:\n  - name: spec-bdd\n")
    write(
        repo / "modules" / "spec-bdd" / "module.yaml",
        "name: spec-bdd\ndescription: BDD 协作规范\nversion: 1.0.0\n",
    )
    write(repo / "modules" / "spec-bdd" / "templates" / "BDDSpec.md.j2", "# BDD\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "发布：准备 0.4.4")

    write(repo / "docs" / "release-process.md", "# 发版流程\n\n补充 release notes 审阅规则。\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "文档：补充发版审阅流程")

    write(repo / "pyproject.toml", '[project]\nname = "agentphilosophy"\nversion = "0.4.5"\n')
    write(repo / "catalog.yaml", "schema_version: 1\ncontent_version: 0.4.5\nmodules:\n  - name: spec-bdd\n")
    write(
        repo / "modules" / "spec-bdd" / "module.yaml",
        "name: spec-bdd\ndescription: BDD 协作规范\nversion: 1.1.0\n",
    )
    write(repo / "modules" / "spec-bdd" / "templates" / "BDDSpec.md.j2", "# BDD\n\n新增失败路径断言。\n")
    write(repo / "tests" / "test_release_notes.py", "def test_notes():\n    assert True\n")

    notes_path = generator.generate_release_notes(repo, "0.4.5", "0.4.5")

    content = notes_path.read_text(encoding="utf-8")
    assert notes_path == repo / "dist" / "release-notes-v0.4.5.md"
    assert "发布 AgentPhilosophy CLI v0.4.5" in content
    assert "默认内容源 `content_version` 升级到 `0.4.5`" in content
    assert "## 本次 diff 重点" in content
    assert "中央内容源" in content
    assert "tests/test_release_notes.py" in content
    assert "## 模块版本变化" in content
    assert "`spec-bdd`：`1.0.0` -> `1.1.0`，BDD 协作规范。" in content
    assert "## 最近提交参考" in content
    assert "文档：补充发版审阅流程" in content
    assert "请补充" not in content


def test_generate_release_notes_uses_reachable_tag_below_target_version(tmp_path: Path) -> None:
    generator = load_generator()
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")

    write(repo / "pyproject.toml", '[project]\nname = "agentphilosophy"\nversion = "0.4.4"\n')
    write(repo / "catalog.yaml", "schema_version: 1\ncontent_version: 0.4.4\nmodules:\n  - name: spec-bdd\n")
    write(
        repo / "modules" / "spec-bdd" / "module.yaml",
        "name: spec-bdd\ndescription: BDD 协作规范\nversion: 1.0.0\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "发布：准备 0.4.4")
    git(repo, "tag", "v0.4.4")

    write(
        repo / "modules" / "spec-bdd" / "module.yaml",
        "name: spec-bdd\ndescription: BDD 协作规范\nversion: 1.1.0\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "功能：升级 BDD 模块")
    git(repo, "tag", "v9.0.0")

    write(repo / "pyproject.toml", '[project]\nname = "agentphilosophy"\nversion = "0.4.5"\n')

    notes_path = generator.generate_release_notes(repo, "0.4.5", "0.4.5")

    content = notes_path.read_text(encoding="utf-8")
    assert "自动摘要基于`v0.4.4` 到当前工作树" in content
    assert "功能：升级 BDD 模块" in content
    assert "`spec-bdd`：`1.0.0` -> `1.1.0`，BDD 协作规范。" in content


def test_generate_release_notes_reports_deleted_modules(tmp_path: Path) -> None:
    generator = load_generator()
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")

    write(repo / "catalog.yaml", "schema_version: 1\ncontent_version: 0.4.4\nmodules:\n  - name: legacy\n")
    write(
        repo / "modules" / "legacy" / "module.yaml",
        "name: legacy\ndescription: 旧模块\nversion: 1.0.0\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "发布：准备 0.4.4")
    git(repo, "tag", "v0.4.4")

    (repo / "modules" / "legacy" / "module.yaml").unlink()
    write(repo / "catalog.yaml", "schema_version: 1\ncontent_version: 0.4.5\nmodules: []\n")

    notes_path = generator.generate_release_notes(repo, "0.4.5", "0.4.5")

    content = notes_path.read_text(encoding="utf-8")
    assert "`legacy`：删除模块，原 version `1.0.0`，旧模块。" in content
