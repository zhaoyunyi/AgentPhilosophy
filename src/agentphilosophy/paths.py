from __future__ import annotations

from pathlib import Path

from .errors import SyncError


def render_inline_template(template: str, context: dict[str, object]) -> str:
    from jinja2 import StrictUndefined
    from jinja2.sandbox import SandboxedEnvironment, SecurityError

    env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)
    try:
        return env.from_string(template).render(**context)
    except SecurityError as exc:
        raise SyncError(f"unsafe inline template expression: {exc}") from exc


def resolve_inside(root: Path, value: str, *, label: str, reject_symlinks: bool = False) -> Path:
    if not value:
        raise SyncError(f"{label} cannot be empty")
    root_resolved = root.resolve()
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root_resolved / raw
    if reject_symlinks:
        try:
            relative = candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise SyncError(f"{label} escapes project root: {value}") from exc
        current = root_resolved
        for part in relative.parts:
            current = current / part
            if part == ".." or current.is_symlink():
                raise SyncError(f"{label} contains a symlink or parent traversal: {value}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SyncError(f"{label} escapes project root: {value}") from exc
    return resolved


def relative_path(root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(root.resolve()).as_posix()


def candidate_file_for(migration_dir: Path, rel_path: str) -> Path:
    safe_name = rel_path.replace("/", "__").replace("..", "__")
    return migration_dir / "diffs" / f"{safe_name}.new"


def candidate_diff_file_for(migration_dir: Path, rel_path: str) -> Path:
    safe_name = rel_path.replace("/", "__").replace("..", "__")
    return migration_dir / "diffs" / f"{safe_name}.diff"
