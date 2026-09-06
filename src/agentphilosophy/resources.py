from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path

from .errors import SyncError
from .paths import resolve_inside

PACKAGED_SOURCE_DIR = "default_source"
LLM_USAGE_MODE_REL_PATHS = {
    "full": Path("docs/cli-usage-for-llm.md"),
    "auto-config": Path("docs/llm-usage-auto-config.md"),
    "user-breakpoints": Path("docs/llm-usage-user-breakpoints.md"),
}
LLM_USAGE_MODE_FORMAT_REL_PATHS = {
    mode: {"markdown": path}
    for mode, path in LLM_USAGE_MODE_REL_PATHS.items()
}
LLM_USAGE_MODE_FORMAT_REL_PATHS["user-breakpoints"]["json"] = Path(
    "docs/llm-usage-user-breakpoints.json"
)


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


def llm_usage_path(source_root: Path, mode: str = "full", output_format: str = "markdown") -> Path | None:
    rel_path = LLM_USAGE_MODE_FORMAT_REL_PATHS.get(mode, {}).get(output_format)
    if rel_path is None:
        return None
    return source_root / rel_path


def read_llm_usage(path: Path) -> str:
    """完整 CLI 输出按入口清单组装；单页仍可由 Agent 按任务读取。"""
    text = path.read_text(encoding="utf-8")
    includes = re.findall(r"<!-- include: (cli/[^\r\n]+) -->", text)
    if not includes:
        return text
    parts = [re.sub(r"<!-- include: cli/[^\r\n]+ -->\n?", "", text).rstrip()]
    for name in dict.fromkeys(includes):
        included = resolve_inside(path.parent / "cli", name.removeprefix("cli/"), label="LLM documentation include")
        if included.suffix != ".md" or not included.is_file():
            raise SyncError(f"LLM documentation include missing or invalid: {name}")
        parts.append(included.read_text(encoding="utf-8").rstrip())
    return "\n\n".join(parts) + "\n"
