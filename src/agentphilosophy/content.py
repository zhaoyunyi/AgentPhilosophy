"""中央内容源的唯一文件清单，供指纹、镜像与打包校验共用。"""

from pathlib import Path

from .errors import SyncError

CONTENT_FILES = (
    "catalog.yaml",
    "docs/cli-usage-for-llm.md",
    "docs/llm-usage-auto-config.md",
    "docs/llm-usage-user-breakpoints.md",
    "docs/llm-usage-user-breakpoints.json",
    "docs/guides/code-review-graph.md",
)
CONTENT_DIRS = ("modules", "presets", "templates", "docs/cli")
IGNORED_NAMES = {".DS_Store", "__pycache__", ".pytest_cache", ".ruff_cache", ".git", ".jj", ".venv"}


def is_content_path(relative: Path) -> bool:
    return not (set(relative.parts) & IGNORED_NAMES) and relative.suffix not in {".pyc", ".pyo"}


def source_files(root: Path) -> list[Path]:
    candidates = [root / name for name in CONTENT_FILES]
    for name in CONTENT_DIRS:
        if (root / name).is_symlink():
            raise SyncError(f"content directory symlink is not supported: {name}")
        if (root / name).is_dir():
            candidates.extend((root / name).rglob("*"))
    files = []
    for path in candidates:
        if not is_content_path(path.relative_to(root)):
            continue
        if path.is_symlink() and path.is_dir():
            raise SyncError(f"content directory symlink is not supported: {path}")
        try:
            path.resolve().relative_to(root.resolve())
        except (ValueError, OSError, RuntimeError) as exc:
            raise SyncError(f"content source escapes root or cannot be resolved: {path}") from exc
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())
