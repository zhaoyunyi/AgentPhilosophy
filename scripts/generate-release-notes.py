#!/usr/bin/env python
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

RELEASE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
RELEASE_NOISE_PATHS = {
    ".agentphilosophy.yaml",
    ".agents/agentphilosophy-state.yaml",
}
RELEASE_NOISE_PREFIXES = (
    ".agents/",
    ".omc/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    ".venv/",
    "dist/",
)
RELEASE_NOISE_PARTS = {"__pycache__"}
RELEASE_NOISE_SUFFIXES = (".pyc", ".pyo")
RELEASE_NOISE_BASENAMES = {".DS_Store"}


def parse_version_tag(tag: str) -> tuple[int, int, int] | None:
    if not RELEASE_TAG_RE.match(tag):
        return None
    major, minor, patch = tag[1:].split(".")
    return int(major), int(minor), int(patch)


def run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(repo_root: Path, args: list[str]) -> str:
    result = run_git(repo_root, args)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def normalize_change_path(path: str) -> str:
    normalized = Path(path).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def managed_output_paths(repo_root: Path) -> set[str]:
    state_path = repo_root / ".agents" / "agentphilosophy-state.yaml"
    if not state_path.is_file():
        return set()

    state = read_yaml_text(state_path.read_text(encoding="utf-8"))
    files = state.get("files") or []
    managed_paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        managed_paths.add(normalize_change_path(str(item["path"])))
    return managed_paths


def is_release_noise_path(path: str) -> bool:
    normalized = normalize_change_path(path)
    parts = normalized.split("/")
    if normalized in RELEASE_NOISE_PATHS:
        return True
    if normalized.startswith(RELEASE_NOISE_PREFIXES):
        return True
    if any(part in RELEASE_NOISE_PARTS for part in parts):
        return True
    if any(part.endswith(".egg-info") for part in parts):
        return True
    if parts[-1] in RELEASE_NOISE_BASENAMES:
        return True
    return normalized.endswith(RELEASE_NOISE_SUFFIXES)


def is_release_relevant_path(path: str, managed_paths: set[str]) -> bool:
    normalized = normalize_change_path(path)
    return normalized not in managed_paths and not is_release_noise_path(normalized)


def is_ancestor(repo_root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    result = run_git(repo_root, ["merge-base", "--is-ancestor", ancestor, descendant])
    return result.returncode == 0


def previous_release_tag(repo_root: Path, version: str) -> str | None:
    target_version = parse_version_tag(f"v{version}")
    if target_version is None:
        return None

    output = git_output(repo_root, ["tag", "--list", "v[0-9]*", "--sort=-v:refname"])
    candidates: list[tuple[int, int, int, str]] = []
    for tag in output.splitlines():
        tag = tag.strip()
        parsed = parse_version_tag(tag)
        if parsed is not None and parsed < target_version and is_ancestor(repo_root, tag):
            candidates.append((*parsed, tag))
    if not candidates:
        return None
    return max(candidates)[3]


def changed_files(repo_root: Path, base_ref: str | None) -> list[tuple[str, str]]:
    args = ["diff", "--name-status", "--no-renames"]
    if base_ref:
        args.append(base_ref)
    else:
        args.append("HEAD")
    args.append("--")

    output = git_output(repo_root, args)
    managed_paths = managed_output_paths(repo_root)
    changes: list[tuple[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], normalize_change_path(parts[-1])
        if not is_release_relevant_path(path, managed_paths):
            continue
        changes.append((status, path))

    tracked_paths = {path for _status, path in changes}
    status_output = git_output(repo_root, ["status", "--porcelain", "--untracked-files=all"])
    for line in status_output.splitlines():
        if not line.startswith("?? "):
            continue
        path = normalize_change_path(line[3:])
        if path in tracked_paths or not is_release_relevant_path(path, managed_paths):
            continue
        changes.append(("??", path))
    return changes


def recent_commit_subjects(repo_root: Path, base_ref: str | None) -> list[str]:
    args = ["log", "--format=%s"]
    if base_ref:
        args.append(f"{base_ref}..HEAD")
    else:
        args.extend(["-n", "8"])
    output = git_output(repo_root, args)

    subjects: list[str] = []
    seen: set[str] = set()
    for subject in output.splitlines():
        subject = subject.strip()
        if not subject or subject in seen:
            continue
        seen.add(subject)
        subjects.append(subject)
    return subjects[:8]


def read_yaml_text(text: str) -> dict[str, Any]:
    value = yaml.safe_load(text) or {}
    if not isinstance(value, dict):
        return {}
    return value


def file_at_ref(repo_root: Path, ref: str, relative_path: Path) -> str | None:
    result = run_git(repo_root, ["show", f"{ref}:{relative_path.as_posix()}"])
    if result.returncode != 0:
        return None
    return result.stdout


def module_paths_at_ref(repo_root: Path, ref: str) -> set[Path]:
    output = git_output(repo_root, ["ls-tree", "-r", "--name-only", ref, "--", "modules"])
    return {
        Path(line.strip())
        for line in output.splitlines()
        if line.strip().endswith("/module.yaml")
    }


def module_version_changes(repo_root: Path, base_ref: str | None) -> list[tuple[str, str | None, str | None, str]]:
    compare_ref = base_ref or "HEAD"
    changes: list[tuple[str, str | None, str | None, str]] = []

    current_paths = {
        module_path.relative_to(repo_root)
        for module_path in (repo_root / "modules").glob("*/module.yaml")
    }
    previous_paths = module_paths_at_ref(repo_root, compare_ref)

    for relative_path in sorted(current_paths | previous_paths, key=lambda path: path.as_posix()):
        module_path = repo_root / relative_path
        current: dict[str, Any] = {}
        current_version: str | None = None
        if module_path.is_file():
            current = read_yaml_text(module_path.read_text(encoding="utf-8"))
            current_version_value = current.get("version")
            current_version = str(current_version_value) if current_version_value is not None else None

        current_name = str(current.get("name") or module_path.parent.name)
        description = str(current.get("description") or current_name)

        previous_text = file_at_ref(repo_root, compare_ref, relative_path)
        previous_version: str | None = None
        previous_name: str | None = None
        previous_description: str | None = None
        if previous_text is not None:
            previous = read_yaml_text(previous_text)
            previous_name = str(previous.get("name") or module_path.parent.name)
            previous_description = str(previous.get("description") or previous_name)
            previous_version_value = previous.get("version")
            previous_version = str(previous_version_value) if previous_version_value is not None else None

        if current_version is None and previous_version is not None:
            changes.append((
                previous_name or current_name,
                previous_version,
                None,
                previous_description or description,
            ))
            continue
        if current_version is None:
            continue

        if previous_version != current_version:
            changes.append((current_name, previous_version, current_version, description))

    return changes


def category_for(path: str) -> str:
    if path in {"pyproject.toml", "uv.lock", "sync.py"} or path.startswith("scripts/"):
        return "CLI/脚本"
    if path.startswith("src/agentphilosophy/") and not path.startswith("src/agentphilosophy/default_source/"):
        return "CLI/脚本"
    if (
        path == "catalog.yaml"
        or path.startswith("modules/")
        or path.startswith("presets/")
        or path.startswith("src/agentphilosophy/default_source/")
    ):
        return "中央内容源"
    if path.startswith("tests/") or path.startswith(".github/"):
        return "测试/验证"
    if path in {"README.md", "AGENTS.md", "CLAUDE.md"} or path.startswith("docs/"):
        return "文档"
    return "其他"


def format_paths(paths: list[str], limit: int = 6) -> str:
    selected = paths[:limit]
    formatted = "、".join(f"`{path}`" for path in selected)
    remaining = len(paths) - len(selected)
    if remaining > 0:
        formatted += f" 等 {remaining} 个文件"
    return formatted


def diff_summary_lines(changes: list[tuple[str, str]]) -> list[str]:
    if not changes:
        return ["- 未检测到当前工作树中的版本相关 diff；本摘要主要参考最近提交。"]

    grouped: dict[str, list[str]] = {}
    for _status, path in changes:
        grouped.setdefault(category_for(path), []).append(path)

    lines: list[str] = []
    for category in ["CLI/脚本", "中央内容源", "测试/验证", "文档", "其他"]:
        paths = grouped.get(category)
        if not paths:
            continue
        lines.append(f"- {category}：{format_paths(paths)}。")
    return lines


def module_change_lines(changes: list[tuple[str, str | None, str | None, str]]) -> list[str]:
    if not changes:
        return ["- 未检测到 `modules/*/module.yaml` 的模块版本变化。"]

    lines: list[str] = []
    for name, old_version, new_version, description in changes:
        if new_version is None:
            lines.append(f"- `{name}`：删除模块，原 version `{old_version}`，{description}。")
        elif old_version is None:
            lines.append(f"- `{name}`：新增 `version` `{new_version}`，{description}。")
        else:
            lines.append(f"- `{name}`：`{old_version}` -> `{new_version}`，{description}。")
    return lines


def dependency_impact_lines(
    version: str,
    content_version: str,
    module_changes: list[tuple[str, str | None, str | None, str]],
    changes: list[tuple[str, str]],
) -> list[str]:
    lines = [
        "- `agentphilosophy_version` 会写入依赖项目的同步状态。",
        "- `source_content_version` 用于提示依赖项目是否需要同步新一轮中央内容。",
    ]
    if version != content_version:
        lines.append(f"- 本次 CLI 版本为 `{version}`，内容源版本为 `{content_version}`，审阅时需分别核对两条版本线。")

    if any(category_for(path) == "中央内容源" for _status, path in changes):
        lines.append("- 默认内容源有文件变化，依赖项目同步前先运行 `push --dry-run` 审查托管输出计划。")

    if module_changes:
        modules = "、".join(f"`{name}`" for name, _old, _new, _description in module_changes[:6])
        lines.append(f"- 依赖项目可能看到 `module version stale`，优先审查 {modules} 对应输出。")
    else:
        lines.append("- 未检测到单模块版本升级，依赖项目主要关注 CLI 与内容源版本 stale 提示。")

    lines.append("- 发版后运行 `uv run sync.py status` 查看 registry 中依赖项目是否 stale。")
    return lines


def generate_release_notes(repo_root: Path, version: str, content_version: str) -> Path:
    repo_root = repo_root.resolve()
    base_ref = previous_release_tag(repo_root, version)
    changes = changed_files(repo_root, base_ref)
    module_changes = module_version_changes(repo_root, base_ref)
    commits = recent_commit_subjects(repo_root, base_ref)
    changed_categories = sorted({category_for(path) for _status, path in changes})

    basis = f"`{base_ref}` 到当前工作树" if base_ref else "当前工作树相对 `HEAD`"
    category_text = "、".join(changed_categories) if changed_categories else "最近提交"

    summary_lines = [
        f"- 发布 AgentPhilosophy CLI v{version}。",
        f"- 默认内容源 `content_version` 升级到 `{content_version}`。",
        f"- 自动摘要基于{basis}、模块版本变化和最近提交生成。",
    ]
    if changes:
        summary_lines.append(f"- 本次版本相关 diff 涉及 `{len(changes)}` 个文件，主要集中在 {category_text}。")
    if module_changes:
        module_names = "、".join(f"`{name}`" for name, _old, _new, _description in module_changes[:6])
        summary_lines.append(f"- 检测到模块版本变化：{module_names}。")
    if commits:
        summary_lines.append(f"- 最近提交参考：{commits[0]}。")

    commit_lines = [f"- {subject}" for subject in commits] or ["- 未检测到可用的最近提交记录。"]

    lines = [
        "## 变更摘要",
        "",
        *summary_lines,
        "",
        "## 本次 diff 重点",
        "",
        *diff_summary_lines(changes),
        "",
        "## 模块版本变化",
        "",
        *module_change_lines(module_changes),
        "",
        "## 最近提交参考",
        "",
        *commit_lines,
        "",
        "## 依赖项目影响",
        "",
        *dependency_impact_lines(version, content_version, module_changes, changes),
        "",
        "## 验证",
        "",
        "- `uv run ruff check .`",
        "- `uv run pytest -q`",
        "- `uv run sync.py validate`",
        "- `uv build`",
        f"- `bash scripts/release-smoke.sh dist/agentphilosophy-{version}-py3-none-any.whl`",
        "",
    ]

    output_path = repo_root / "dist" / f"release-notes-v{version}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate AgentPhilosophy release notes from local release context.")
    parser.add_argument("version")
    parser.add_argument("--content-version", default=None)
    args = parser.parse_args(argv)

    output_path = generate_release_notes(Path.cwd(), args.version, args.content_version or args.version)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
