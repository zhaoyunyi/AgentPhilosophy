from __future__ import annotations

from pathlib import Path
from typing import Any

from .hashing import sha256_file, source_revision, source_tree_hash
from .project import DEFAULT_PATHS
from .yamlio import read_yaml, write_yaml


def state_path(project_root: Path) -> Path:
    return project_root / DEFAULT_PATHS["agent_work_dir"] / "agentphilosophy-state.yaml"


def empty_state(source_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source": str(source_root),
        "source_revision": source_revision(source_root),
        "source_tree_hash": source_tree_hash(source_root),
        "modules": {},
        "files": [],
    }


def load_state(project_root: Path, source_root: Path) -> dict[str, Any]:
    path = state_path(project_root)
    if not path.exists():
        return empty_state(source_root)
    state = read_yaml(path)
    state.setdefault("modules", {})
    state.setdefault("files", [])
    return state


def write_state(project_root: Path, state: dict[str, Any]) -> None:
    write_yaml(state_path(project_root), state)


def state_file_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = state.get("files") or []
    return {str(item["path"]): item for item in files if isinstance(item, dict) and item.get("path")}


def has_manual_edit(project_root: Path, record: dict[str, Any]) -> bool:
    file_path = project_root / str(record["path"])
    if not file_path.exists():
        return True
    return sha256_file(file_path) != record.get("last_written_hash")
