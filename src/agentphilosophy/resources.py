from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path

PACKAGED_SOURCE_DIR = "default_source"
LLM_USAGE_MODE_REL_PATHS = {
    "full": Path("docs/cli-usage-for-llm.md"),
    "auto-config": Path("docs/llm-usage-auto-config.md"),
    "user-breakpoints": Path("docs/llm-usage-user-breakpoints.md"),
}


def is_central_source_root(path: Path) -> bool:
    return (
        (path / "catalog.yaml").is_file()
        and (path / "modules").is_dir()
        and (path / "presets").is_dir()
    )


@contextmanager
def resolve_source_root(source: str | None) -> Iterator[Path]:
    if source:
        yield Path(source).expanduser().resolve()
        return

    cwd = Path.cwd().resolve()
    if is_central_source_root(cwd):
        yield cwd
        return

    resource = files("agentphilosophy").joinpath(PACKAGED_SOURCE_DIR)
    with as_file(resource) as packaged_source:
        yield packaged_source


def llm_usage_path(source_root: Path, mode: str = "full") -> Path:
    return source_root / LLM_USAGE_MODE_REL_PATHS[mode]
