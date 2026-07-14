from __future__ import annotations

import shlex
import shutil
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import Report, SyncError
from .hashing import sha256_file
from .paths import relative_path, resolve_inside


def command_update_documentation(
    project_root: Path,
    *,
    project_name: str,
    documentation_paths: object,
    llm_command: str,
    timeout_seconds: int,
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    changed_outputs: list[str],
) -> Report:
    report = Report()
    try:
        paths = _validated_documentation_paths(project_root, documentation_paths)
        command = _validated_llm_command(llm_command)
    except (SyncError, ValueError) as exc:
        report.error(str(exc))
        return report

    try:
        project_before = _project_snapshot(project_root)
        protected_before = _protected_file_snapshot(project_root)
        vcs_before = _version_control_metadata_snapshot(project_root)
    except (OSError, SyncError, subprocess.SubprocessError) as exc:
        report.error(f"cannot snapshot project before LLM documentation update: {exc}")
        return report
    vcs_symlinks = sorted(
        path for path, fingerprint in vcs_before.items() if fingerprint.startswith("symlink:")
    )
    if vcs_symlinks:
        report.error(f"version-control metadata contains symlinks: {', '.join(vcs_symlinks)}")
        return report
    allowed_symlinks = sorted(
        path
        for path, fingerprint in project_before.items()
        if fingerprint.startswith("symlink:") and _path_is_allowed(project_root, path, paths)
    )
    if allowed_symlinks:
        report.error(f"documentation_paths contain symlinks: {', '.join(allowed_symlinks)}")
        return report
    prompt = _documentation_prompt(
        project_name=project_name,
        documentation_paths=[relative_path(project_root, path) for path in paths],
        previous_state=previous_state,
        current_state=current_state,
        changed_outputs=changed_outputs,
    )

    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        report.error(f"LLM command not found: {command[0]}")
    except subprocess.TimeoutExpired:
        report.error(f"LLM documentation update timed out after {timeout_seconds}s")
    except OSError as exc:
        report.error(f"LLM documentation update could not start: {exc}")
    else:
        if result.returncode != 0:
            diagnostic = _command_diagnostic(result.stderr or result.stdout)
            detail = f": {diagnostic}" if diagnostic else ""
            report.error(f"LLM documentation update failed with exit code {result.returncode}{detail}")

    try:
        project_after = _project_snapshot(project_root)
        protected_after = _protected_file_snapshot(project_root)
        vcs_after = _version_control_metadata_snapshot(project_root)
    except (OSError, SyncError, subprocess.SubprocessError) as exc:
        report.error(f"cannot snapshot project after LLM documentation update: {exc}")
        return report

    changed_project_files = sorted(
        path
        for path in set(project_before) | set(project_after)
        if project_before.get(path) != project_after.get(path)
    )
    changed_symlinks = sorted(
        path
        for path in changed_project_files
        if project_before.get(path, "").startswith("symlink:")
        or project_after.get(path, "").startswith("symlink:")
    )
    changed_docs = sorted(
        path
        for path in changed_project_files
        if path not in changed_symlinks and _path_is_allowed(project_root, path, paths)
    )
    if changed_docs:
        report.info(f"documentation updated: {', '.join(changed_docs)}")
    elif report.ok:
        report.warn("LLM completed without documentation changes")

    protected_names = set(protected_before) | set(protected_after)
    managed_names = {
        str(item["path"])
        for item in current_state.get("files") or []
        if isinstance(item, dict) and item.get("path")
    }
    outside_paths = sorted(
        path
        for path in changed_project_files
        if path not in protected_names
        and path not in managed_names
        and not _path_is_allowed(project_root, path, paths)
    )
    if outside_paths:
        report.error(f"LLM changed files outside documentation_paths: {', '.join(outside_paths)}")
    if changed_symlinks:
        report.error(f"LLM changed symlinks: {', '.join(changed_symlinks)}")

    managed_drift = _managed_file_drift(project_root, current_state)
    if managed_drift:
        report.error(f"LLM changed managed files: {', '.join(managed_drift)}")
    protected_drift = sorted(
        path
        for path in set(protected_before) | set(protected_after)
        if protected_before.get(path) != protected_after.get(path)
    )
    if protected_drift:
        report.error(f"LLM changed protected files: {', '.join(protected_drift)}")
    if vcs_before != vcs_after:
        report.error("LLM changed version-control metadata")
    return report


def documentation_refresh_needed(
    current_state: dict[str, Any],
    changed_outputs: list[str],
    documentation_paths: object,
) -> bool:
    if changed_outputs:
        return True
    refresh = current_state.get("documentation_refresh")
    if not isinstance(refresh, dict):
        return True
    for key in (
        "agentphilosophy_version",
        "source_content_version",
        "source_tree_hash",
        "modules",
    ):
        if refresh.get(key) != current_state.get(key):
            return True
    return refresh.get("documentation_paths") != _documentation_path_fingerprint(documentation_paths)


def mark_documentation_refreshed(state: dict[str, Any], documentation_paths: object) -> None:
    state["documentation_refresh"] = {
        "agentphilosophy_version": state.get("agentphilosophy_version"),
        "source_content_version": state.get("source_content_version"),
        "source_tree_hash": state.get("source_tree_hash"),
        "modules": dict(state.get("modules") or {}),
        "documentation_paths": _documentation_path_fingerprint(documentation_paths),
        "last_refreshed": datetime.now(UTC).isoformat(),
    }


def _validated_documentation_paths(project_root: Path, raw_paths: object) -> list[Path]:
    if not isinstance(raw_paths, list) or not raw_paths:
        raise SyncError("registry documentation_paths must be a non-empty list")

    paths: list[Path] = []
    for raw_path in raw_paths:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise SyncError("registry documentation_paths entries must be non-empty strings")
        value = raw_path.strip()
        if Path(value).expanduser().is_absolute():
            raise SyncError(f"documentation path must be relative to project root: {value}")
        target = resolve_inside(project_root, value, label="documentation path")
        normalized = relative_path(project_root, target)
        first_part = Path(normalized).parts[0] if Path(normalized).parts else ""
        if first_part in {".agents", ".git", ".jj", ".codex", ".claude", "skills"}:
            raise SyncError(f"documentation path uses a protected project area: {value}")
        if normalized in {".agentphilosophy.yaml", "AGENTS.md", "CLAUDE.md"}:
            raise SyncError(f"documentation path is protected: {value}")
        if target == project_root.resolve():
            raise SyncError("documentation path cannot be the project root")
        paths.append(target)
    return sorted(set(paths), key=lambda path: relative_path(project_root, path))


def _validated_llm_command(value: str) -> list[str]:
    command = shlex.split(value)
    if not command:
        raise SyncError("LLM command cannot be empty")
    if command[0] != "codex":
        raise SyncError("LLM command must invoke the trusted PATH executable as 'codex'")
    executable = shutil.which("codex")
    if executable is None:
        raise SyncError("LLM command not found: codex")
    if len(command) < 3 or command[1] != "exec":
        raise SyncError(
            "LLM command requires sandboxed Codex exec with --ephemeral, "
            "--ignore-user-config, and --sandbox workspace-write"
        )

    arguments = command[2:]
    sandbox_values: list[str] = []
    for index, argument in enumerate(arguments):
        if argument in {"-s", "--sandbox"}:
            sandbox_values.append(arguments[index + 1] if index + 1 < len(arguments) else "")
        elif argument.startswith("--sandbox="):
            sandbox_values.append(argument.split("=", 1)[1])
    if sandbox_values != ["workspace-write"]:
        raise SyncError(
            "LLM command requires exactly one workspace-write sandbox and forbids sandbox overrides"
        )

    seen: set[str] = set()
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in {"--ephemeral", "--ignore-user-config", "--skip-git-repo-check"}:
            key = argument
            index += 1
        elif argument in {"-s", "--sandbox", "-m", "--model"}:
            if index + 1 >= len(arguments) or not arguments[index + 1]:
                raise SyncError("LLM command has an option without a value")
            key = "sandbox" if argument in {"-s", "--sandbox"} else "model"
            index += 2
        elif argument.startswith("--sandbox="):
            key = "sandbox"
            index += 1
        elif argument.startswith("--model=") and argument.split("=", 1)[1]:
            key = "model"
            index += 1
        elif argument == "-" and index == len(arguments) - 1:
            key = "stdin-prompt"
            index += 1
        else:
            raise SyncError(
                "LLM command contains unsupported or unsafe Codex arguments; "
                "no extra writable roots or config overrides are allowed"
            )
        if key in seen:
            raise SyncError(f"LLM command repeats Codex option: {key}")
        seen.add(key)

    if not {"--ephemeral", "--ignore-user-config", "sandbox", "stdin-prompt"}.issubset(seen):
        raise SyncError(
            "LLM command requires sandboxed Codex exec with --ephemeral, "
            "--ignore-user-config, --sandbox workspace-write, no extra writable roots, "
            "and '-' as the stdin prompt"
        )
    command[0] = executable
    return command


def _documentation_path_fingerprint(raw_paths: object) -> list[str]:
    if not isinstance(raw_paths, list):
        return []
    return sorted(
        {item.strip() for item in raw_paths if isinstance(item, str) and item.strip()}
    )


def _project_snapshot(project_root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in _project_files(project_root):
        rel_path = path.relative_to(project_root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            snapshot[rel_path] = f"symlink:{mode:o}:{path.readlink()}"
        elif path.is_file():
            snapshot[rel_path] = f"file:{mode:o}:{sha256_file(path)}"
    return snapshot


def _project_files(project_root: Path) -> list[Path]:
    return sorted(
        path
        for path in project_root.rglob("*")
        if (path.is_file() or path.is_symlink())
        and not {".git", ".jj"}.intersection(path.relative_to(project_root).parts)
    )


def _path_is_allowed(project_root: Path, rel_path: str, allowed_paths: list[Path]) -> bool:
    candidate = Path(rel_path)
    allowed_rel_paths = [allowed.relative_to(project_root.resolve()) for allowed in allowed_paths]
    return any(candidate == allowed or allowed in candidate.parents for allowed in allowed_rel_paths)


def _command_diagnostic(value: str, *, limit: int = 600) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= limit:
        return compact
    return "..." + compact[-limit:]


def _protected_file_snapshot(project_root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for rel_path in (
        ".agentphilosophy.yaml",
        ".agents/agentphilosophy-state.yaml",
    ):
        path = project_root / rel_path
        if path.is_file():
            snapshot[rel_path] = sha256_file(path)
    return snapshot


def _version_control_metadata_snapshot(project_root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    _snapshot_metadata_path(snapshot, "project/.git", project_root / ".git")

    git_dirs: list[tuple[str, Path]] = []
    for label, arguments in (
        ("git-dir", ["git", "rev-parse", "--path-format=absolute", "--git-dir"]),
        ("git-common-dir", ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"]),
    ):
        result = subprocess.run(
            arguments,
            cwd=project_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            git_dirs.append((label, Path(result.stdout.strip())))

    unique_git_dirs: dict[Path, str] = {}
    for label, root in git_dirs:
        unique_git_dirs.setdefault(root.resolve(), label)
    for root, label in unique_git_dirs.items():
        _snapshot_metadata_tree(
            snapshot,
            label,
            root,
            excluded_top_level={"objects", "logs"},
        )

    jj_root = project_root / ".jj"
    jj_repo = jj_root / "repo"
    repo_root = jj_repo
    if jj_repo.is_file():
        _snapshot_metadata_path(snapshot, "jj/repo", jj_repo)
        try:
            repo_root = (jj_root / jj_repo.read_text(encoding="utf-8").strip()).resolve()
        except (OSError, UnicodeError):
            repo_root = jj_repo

    _snapshot_metadata_tree(snapshot, "jj/working_copy", jj_root / "working_copy")
    if repo_root.is_dir():
        _snapshot_metadata_tree(
            snapshot,
            "jj/repo",
            repo_root,
            excluded_top_level={"index", "op_store", "store", "submodule_store"},
        )
    return snapshot


def _snapshot_metadata_path(snapshot: dict[str, str], label: str, path: Path) -> None:
    if path.is_symlink():
        snapshot[label] = f"symlink:{path.readlink()}"
    elif path.is_file():
        snapshot[label] = sha256_file(path)


def _snapshot_metadata_tree(
    snapshot: dict[str, str],
    label: str,
    root: Path,
    *,
    excluded_top_level: set[str] | None = None,
) -> None:
    if not root.is_dir():
        _snapshot_metadata_path(snapshot, label, root)
        return
    excluded_top_level = excluded_top_level or set()
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir(), reverse=True):
            relative = path.relative_to(root)
            if relative.parts and relative.parts[0] in excluded_top_level:
                continue
            path_label = f"{label}/{relative.as_posix()}"
            if path.is_symlink() or path.is_file():
                _snapshot_metadata_path(snapshot, path_label, path)
            elif path.is_dir():
                pending.append(path)


def _documentation_prompt(
    *,
    project_name: str,
    documentation_paths: list[str],
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    changed_outputs: list[str],
) -> str:
    previous_modules = previous_state.get("modules") or {}
    current_modules = current_state.get("modules") or {}
    changed_modules = sorted(
        name
        for name in set(previous_modules) | set(current_modules)
        if previous_modules.get(name) != current_modules.get(name)
    )
    managed_files = sorted(
        str(item["path"])
        for item in current_state.get("files") or []
        if isinstance(item, dict) and item.get("path")
    )

    def block(items: list[str]) -> str:
        return "\n".join(f"- `{item}`" for item in items) if items else "- 无"

    previous_cli = previous_state.get("agentphilosophy_version", "unknown")
    current_cli = current_state.get("agentphilosophy_version", "unknown")
    previous_content = previous_state.get("source_content_version", "unknown")
    current_content = current_state.get("source_content_version", "unknown")

    return f"""你正在维护依赖 AgentPhilosophy 的项目 `{project_name}`。
中央规范同步已经成功完成，现在只更新项目自有文档，使其与同步后的当前实现、协作规则和验证入口一致。

## 本轮同步事实

- AgentPhilosophy CLI：{previous_cli} -> {current_cli}
- 中央内容版本：{previous_content} -> {current_content}
- 版本变化模块：{', '.join(changed_modules) if changed_modules else '无'}

本轮新增或更新的托管输出：

{block(changed_outputs)}

## 允许修改的文档范围

{block(documentation_paths)}

## AgentPhilosophy 托管文件

{block(managed_files)}

## 执行要求

1. 先读取项目内适用的 `AGENTS.md`、`CLAUDE.md`、README、相关实现、验证入口和文档索引，以当前仓库事实为准。
2. 只修改“允许修改的文档范围”内的项目自有文档；需要新建文档时也必须位于这些路径内。
3. 不修改 `.agentphilosophy.yaml`、`.agents/`、skills、上面列出的任何托管文件，也不改变代码、配置、依赖或测试。
4. 更新受本轮规则或版本变化影响的说明，删除已经过时的描述；同步维护相关文档索引。
5. 文档只写项目用户和维护者需要理解的当前事实，不暴露内部模型供应商、密钥、原始提示词或运行时敏感信息。
6. 运行适合当前文档范围的只读或验证命令；不要运行 Git 或 jj 命令，不要提交、推送、发布或操作外部环境。
7. 如果当前文档已经准确，无需为了制造改动而改写。
"""


def _managed_file_drift(project_root: Path, state: dict[str, Any]) -> list[str]:
    drift: list[str] = []
    for item in state.get("files") or []:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        rel_path = str(item["path"])
        try:
            path = resolve_inside(project_root, rel_path, label="managed file")
        except SyncError:
            drift.append(rel_path)
            continue
        if not path.is_file() or sha256_file(path) != item.get("last_written_hash"):
            drift.append(rel_path)
    return sorted(drift)
