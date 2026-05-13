from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, StrictUndefined

from .errors import SyncError


def render_inline_template(template: str, context: dict[str, object]) -> str:
    env = Environment(undefined=StrictUndefined, autoescape=False)
    return env.from_string(template).render(**context)


def resolve_inside(root: Path, value: str, *, label: str) -> Path:
    if not value:
        raise SyncError(f"{label} cannot be empty")
    root_resolved = root.resolve()
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root_resolved / raw
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
